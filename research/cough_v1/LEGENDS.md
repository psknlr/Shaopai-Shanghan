# 图表题注

> 由 `scripts/make_tables.py` 生成。图题置于图下、表题置于表上；中英文题名可按目标期刊取舍。

## 图

**图 1　基于 V1 两书版知识图谱的绍派伤寒咳嗽用药规律研究技术路线**  
*Fig. 1　Research framework for mining the cough medication patterns of the Shaopai Shanghan school from the V1 two-book knowledge graph*  
注：左列为医案筛选与规范化流程，右列为《俞根初临证经验集要》中的肺系咳喘方证（判读规则与逐条结果见附表 S6）；①–⑥为分析模块，结果分别见图 2–图 9 与表 2–表 6，理法互证见表 7。  
文件：`figures/fig01_research_framework.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 2　125 例咳嗽医案高频药物的使用频次与功效分类**  
*Fig. 2　Frequency of the most-used herbs and distribution of efficacy categories in 125 cough cases*  
注：A. 使用频次前 30 位药物，柱长为使用频率，柱端数字为医案数，蓝色为化痰止咳平喘药；B. 各功效类别所占药次比例（共 1,519 药次），功效分类依《中药学》教材，未归类者为基原或功效待考药物。  
文件：`figures/fig02_herb_frequency_efficacy.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 3　咳嗽医案用药的四气、五味与归经分布**  
*Fig. 3　Four natures, five flavours and meridian tropism of the herbs used in the cough cases*  
注：以药次计，共 1,437 药次（占单味药药次的 94.6%，性味待考者未计）；A. 四气（微寒、大寒并入寒，微温并入温）；B. 五味；C. 归经。一药多味、多经者分别计入，故五味、归经合计超过 100%。  
文件：`figures/fig03_nature_flavor_meridian.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 4　高频药物单次处方剂量分布与用药特色**  
*Fig. 4　Single-prescription doses of high-frequency herbs and characteristic medication practices*  
注：A. 每点为一条剂量记录（钱，以 2 为底的对数坐标），灰色粗线为四分位间距，黑色竖线为中位数，竖直参考线为 3 钱；B. 五项用药特色的医案占比。1 钱 ≈ 3 g。逐药统计见表 3。  
文件：`figures/fig04_dose_and_features.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 5　高频药物共现网络**  
*Fig. 5　Co-occurrence network of high-frequency herbs*  
注：33 味高频药物按层次聚类树叶序环形排列，仅显示共现 ≥ 13 案的药对（100 条）；节点大小示使用频次，连线粗细示共现医案数；Louvain 社区划分模块度仅 0.138，故以层次聚类分组（C1–C8，见表 5）着色。  
文件：`figures/fig05_cooccurrence_network.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 6　高频药物层次聚类**  
*Fig. 6　Hierarchical clustering of high-frequency herbs*  
注：A. 聚类树状图（Jaccard 距离，类平均法）；B. 两两 Jaccard 相似系数热图，按树状图叶序排列，方框示按平均轮廓系数确定的 8 个药物组合；共表型相关系数 0.813。  
文件：`figures/fig06_hierarchical_clustering.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 7　不同病机类别咳嗽医案的治法与用药**  
*Fig. 7　Treatment principles and herbs across pathogenesis categories of the cough cases*  
注：A. 按病机关键词归类的医案数（规则见附表 S4）；B. 各类医案中含该治法要素的比例；C. 各类医案中药物使用率。* 单侧 Fisher 精确检验 P < 0.05；** 经 Benjamini–Hochberg 校正 q < 0.05；仅比较 n ≥ 10 的 5 类。  
文件：`figures/fig07_pathogenesis_principle_herb.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 8　咳嗽医案的伴随症状、痰象、舌象与脉象**  
*Fig. 8　Accompanying symptoms, sputum, tongue and pulse features of the cough cases*  
注：A. 伴随症状（前 12 项）；B. 痰象；C. 舌象（有舌诊记录 117 例）；D. 左、右脉象，分别以该侧有记录的医案为分母（右 108 例，左 99 例）。  
文件：`figures/fig08_four_diagnostics.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 9　四诊特征与高频药物的关联（提升度）**  
*Fig. 9　Associations between diagnostic features and high-frequency herbs (lift)*  
注：提升度 = P（用药 | 具该特征）/ P（用药），色阶取对数，红示正关联、蓝示负关联；共现 < 3 案者留白；格内数字为提升度 ≥ 1.5 且共现 ≥ 5 案者；药物为使用频率前 20 位。  
文件：`figures/fig09_feature_herb_lift.pdf`（矢量）、`.png`/`.tif`（600 dpi）

**图 10　典型医案的证据链：从原文到图谱关系与分析要素（案35 肝火冲脑肺干咳）**  
*Fig. 10　Evidence chain of a representative case: from source text to graph relations and analytical elements*  
注：① 原文段落（hlc0265c035）；② 图谱中该案的 18 条关系，均保留原文句、段落编号与段内核验结果；③ 规范化后的分析要素。  
文件：`figures/fig10_evidence_chain_example.pdf`（矢量）、`.png`/`.tif`（600 dpi）

## 表

**表 1　纳入医案的基本特征**  
*Table 1　Characteristics of the included cough cases*  
文件：`tables/T1_case_characteristics.csv`

**表 2　高频药物（使用频率 ≥ 10%）的使用频次与药性（n = 125）**  
*Table 2　Frequency and properties of high-frequency herbs (used in ≥ 10% of cases; n = 125)*  
文件：`tables/T2_high_frequency_herbs.csv`

**表 3　高频药物单次处方剂量**  
*Table 3　Single-prescription doses of high-frequency herbs*  
文件：`tables/T3_dose.csv`

**表 4　高频药物关联规则（最小支持度 20%，最小置信度 70%）**  
*Table 4　Association rules among herbs (minimum support 20%, minimum confidence 70%)*  
文件：`tables/T4_association_rules.csv`

**表 5　高频药物层次聚类所得药物组合**  
*Table 5　Herb groups identified by hierarchical clustering*  
文件：`tables/T5_herb_clusters.csv`

**表 6　不同病机类别咳嗽医案的核心用药与治法**  
*Table 6　Core herbs and treatment principles by pathogenesis category*  
文件：`tables/T6_pathogenesis.csv`

**表 7　俞根初治咳理法与何廉臣咳嗽医案用药的对应（理法互证）**  
*Table 7　Correspondence between Yu Genchu’s principles for cough and the medication patterns in He Lianchen’s cough cases*  
文件：`tables/T7_yu_he_correspondence.csv`

## 附表（supplementary/）

| 编号 | 内容 |
| --- | --- |
| S1 | 原书药名写法与规范药名对照 |
| S2 | 纳入医案清单（编号、原书案名、纳入依据、病机类别、用药、治法） |
| S3 | 药物四气五味归经与功效分类及依据 |
| S4 | 病机类别与治法要素的关键词规则 |
| S5 | 敏感性分析：扩展纳入与主分析的药物频率对照 |
| S6 | 《俞根初临证经验集要》方证逐条判读（与咳嗽的关系、来源性质） |
