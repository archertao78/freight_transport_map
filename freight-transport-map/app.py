# 本文件由vscode插件feffery-dash-snippets初始化生成

import uuid
import time
import json
import dash
import pandas as pd
from dash import html, set_props
import feffery_antd_components as fac
import feffery_utils_components as fuc
import feffery_leaflet_components as flc
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State

app = dash.Dash(
    __name__,
    update_title=None,
    suppress_callback_exceptions=True,
    title="货运分析地图",
)

# 读取地图矢量文件
with open(r"D:\git\freight_transport_map\freight-transport-map/中华人民共和国.json", encoding="utf-8") as f:
    regions = json.load(f)

# 读取示例货运计划数据
freight_plans = pd.read_csv(r"D:\git\freight_transport_map\freight-transport-map/示例数据.csv")

app.layout = fuc.FefferyTopProgress(
    fac.AntdCenter(
        [
            # 全局消息提示
            fac.Fragment(id="global-message"),
            # 主面板
            fuc.FefferyDiv(
                [
                    fac.AntdSpace(
                        [
                            fac.AntdSpace(
                                [
                                    # 工具logo
                                    html.Img(src="/assets/imgs/logo.svg", height=64),
                                    # 工具标题
                                    fac.AntdText(
                                        "货运分析地图",
                                        style=style(fontSize=32),
                                    ),
                                ]
                            ),
                            # 工具说明
                            fac.AntdText(
                                "针对全国不同区域间的货运情况进行可视化展示，建议不要选择过多的地区，以便更好地展示结果",
                                type="secondary",
                            ),
                        ],
                        direction="vertical",
                        size=0,
                    ),
                    fac.AntdDivider(),
                    # 工具输入
                    fac.AntdRow(
                        [
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdSelect(
                                        id="departure-regions",
                                        placeholder="请选择",
                                        options=freight_plans["出发地区"]
                                        .unique()
                                        .tolist(),
                                        mode="multiple",
                                        maxTagCount="responsive",
                                    ),
                                    label="出发地",
                                    layout="vertical",
                                    style=style(margin=0),
                                ),
                                span=12,
                            ),
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdSelect(
                                        id="destination-regions",
                                        placeholder="请选择",
                                        options=freight_plans["到达地区"]
                                        .unique()
                                        .tolist(),
                                        mode="multiple",
                                        maxTagCount="responsive",
                                    ),
                                    label="目的地",
                                    layout="vertical",
                                    style=style(margin=0),
                                ),
                                span=12,
                            ),
                            fac.AntdCol(
                                fac.AntdButton(
                                    "查询分析",
                                    id="submit-button",
                                    type="primary",
                                    block=True,
                                    loadingChildren="分析中",
                                ),
                                span=24,
                            ),
                        ],
                        gutter=[5, 8],
                    ),
                    fac.AntdDivider(),
                    # 结果展示区
                    fac.AntdSpin(
                        html.Div(
                            flc.LeafletMap(
                                [flc.LeafletTileLayer()],
                                center={
                                    "lat": 35.134386211514155,
                                    "lng": 106.91839944442702,
                                },
                                zoom=4,
                                viewAutoCorrection=True,
                                style=style(height="100%"),
                            ),
                            id="result-container",
                            style=style(height="calc(100vh - 490px)"),
                        ),
                        text="拼命计算中...",
                        size="large",
                        listenPropsMode="include",
                        includeProps=[
                            "result-container.children",
                        ],
                    ),
                ],
                # 主面板基础样式
                style=style(
                    border="1px solid #dedede",
                    borderRadius=20,
                    backgroundColor="#fff",
                    width="90vw",
                    boxShadow="50px 50px 100px 10px rgba(0,0,0,.1)",
                    minWidth=600,
                    maxWidth=1200,
                    minHeight="calc(100vh - 120px)",
                    boxSizing="border-box",
                    padding="35px 28px",
                ),
            ),
        ],
        # 根容器基础样式
        style=style(
            backgroundColor="#fafafa",
            paddingTop=60,
            paddingBottom=60,
        ),
    ),
    listenPropsMode="include",
    includeProps=[
        "result-container.children",
    ],
    minimum=0.4,
)


@app.callback(
    Output("result-container", "children"),
    Input("submit-button", "nClicks"),
    [State("departure-regions", "value"), State("destination-regions", "value")],
    running=[(Output("submit-button", "loading"), True, False)],
    prevent_initial_call=True,
)
def update_result(nClicks, departure_regions, destination_regions):
    """处理地区选择及分析结果刷新"""

    if not (departure_regions and destination_regions):
        set_props(
            "global-message",
            {"children": fac.AntdMessage(content="请先完善查询条件", type="warning")},
        )

    else:
        # 增加一点加载动画时长
        time.sleep(0.5)

        # 提取目标货运记录数据
        match_freight_plans = (
            freight_plans.query(
                "出发地区==@departure_regions and 到达地区==@destination_regions"
            )
            .groupby(["出发地区", "到达地区"], as_index=False)
            .agg(
                {
                    "出发地区经度": "first",
                    "出发地区纬度": "first",
                    "到达地区经度": "first",
                    "到达地区纬度": "first",
                    "出发时间": "count",
                }
            )
            .rename(columns={"出发时间": "货运班次"})
            .sort_values("货运班次", ascending=False)
        )

        # 聚合统计
        flowData = [
            {
                "from": {
                    "lng": flow["出发地区经度"],
                    "lat": flow["出发地区纬度"],
                },
                "to": {
                    "lng": flow["到达地区经度"],
                    "lat": flow["到达地区纬度"],
                },
                "labels": {
                    "from": flow["出发地区"],
                    "to": flow["到达地区"],
                },
                "value": flow["货运班次"],
            }
            for flow in match_freight_plans.to_dict("records")
        ]

        # 刷新地图
        return fac.AntdRow(
            [
                fac.AntdCol(
                    flc.LeafletMap(
                        [
                            flc.LeafletTileLayer(),
                            # 流线图层
                            flc.LeafletFlowLayer(
                                flowData=flowData,
                                arcLabelFontSize="16px",
                                keepUniqueLabels=True,
                            ),
                            # 相关区域矢量图层
                            flc.LeafletGeoJSON(
                                data={
                                    **regions,
                                    "features": [
                                        region
                                        for region in regions["features"]
                                        if region["properties"]["name"]
                                        in departure_regions
                                        or region["properties"]["name"]
                                        in destination_regions
                                    ],
                                },
                                defaultStyle={"fillOpacity": 0.1, "weight": 2},
                            ),
                        ],
                        key=str(uuid.uuid4()),
                        viewAutoCorrection=True,
                        style=style(height="100%"),
                    ),
                    flex="auto",
                ),
                fac.AntdCol(
                    html.Div(
                        fac.AntdTable(
                            data=match_freight_plans[
                                ["出发地区", "到达地区", "货运班次"]
                            ].to_dict("records"),
                            columns=[
                                {
                                    "dataIndex": "出发地区",
                                    "title": "出发地区",
                                },
                                {
                                    "dataIndex": "到达地区",
                                    "title": "到达地区",
                                },
                                {
                                    "dataIndex": "货运班次",
                                    "title": "货运班次",
                                },
                            ],
                            tableLayout="fixed",
                            size="small",
                            pagination=False,
                            sortOptions={"sortDataIndexes": ["货运班次"]},
                            summaryRowContents=(
                                # 仅在多地区时渲染总结栏
                                [
                                    {
                                        "content": fac.AntdText(
                                            "总计班次：{}".format(
                                                match_freight_plans["货运班次"].sum()
                                            ),
                                            strong=True,
                                        ),
                                        "colSpan": 3,
                                        "align": "center",
                                    },
                                ]
                                if match_freight_plans.shape[0] > 1
                                else []
                            ),
                        ),
                        style=style(height="100%", width=300, overflowY="auto"),
                    ),
                    flex="none",
                ),
            ],
            wrap=False,
            gutter=3,
            style=style(height="100%"),
        )

    return dash.no_update


if __name__ == "__main__":
    app.run(debug=False)
