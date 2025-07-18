~ Command `ProCmdModelNew` 
~ Select `new` `Part`
~ Activate `new` `name_en`
~ Update `new` `name_en` `stainless_steel_cylinder_3x10cm`
~ Activate `new` `ok`

~ 创建基准平面
~ Command `ProCmdDatumPlaneCreate` 
~ Select `datum_plane_0` `Flip`
~ Activate `datum_plane_0` `ok`

~ 创建草图
~ Command `ProCmdSketcherCreate` 
~ Select `sketch_0` `Sketch`
~ Activate `sketch_0` `ok`

~ 绘制圆形
~ Command `ProCmdSketcherCircle` 
~ Select `circle_0` `CenterPoint` 1 `0` `0`
~ Select `circle_0` `EdgePoint` 1 `15.0` `0`

~ 退出草图
~ Command `ProCmdSketcherExit` 

~ 拉伸特征
~ Command `ProCmdExtrudeCreate` 
~ Update `extrude_0` `depth` `100.0`
~ Activate `extrude_0` `ok`

~ 设置材料属性
~ Command `ProCmdMaterialAssign`
~ Update `material` `name` `不锈钢`
~ Activate `material` `ok`

~ 保存模型
~ Command `ProCmdModelSave` 

~ 注释：模型参数
~ 直径: 30.0mm
~ 高度: 100.0mm
~ 材料: 不锈钢
~ 体积: 70.69 cm³