"""PPT-verified source mapping for one semantically labeled design per page."""

# name, base event ID, chapter menu,
# (PPT media ID, Chinese caption, English caption, semantic image kind).
# A reference is a complete screenshot whose on-screen role must be converted
# before it becomes the finished design discussed by the surrounding topic.
GALLERIES = [
    ('tank_intro', 501, 500, [
        (116, '设计按钮位置：它决定坦克、自火、坦歼、防空车或喷火坦克角色', 'Role button: selects tank, SPG, TD, SPAA, or flame-tank role', 'partial'),
        (117, '坦歼与自行火炮角色选择界面', 'Tank-destroyer and SPG role selection', 'partial'),
        (118, '自行防空炮与喷火坦克角色选择界面', 'SPAA and flame-tank role selection', 'partial'),
    ]),
    ('tank_light', 502, 500, [
        (121, '亚洲战场初期战间期中型底盘完整设计', 'Complete early-Asian-theater interwar medium-chassis design', 'complete'),
    ]),
    ('tank_medium', 503, 500, [
        (122, '39年中型榴弹炮主力坦克完整设计', 'Complete 1939 medium-howitzer main tank', 'complete'),
        (124, '步兵坦克MIO的速度修正位置', 'Infantry-tank MIO speed modifier', 'partial'),
    ]),
    ('tank_spg', 504, 500, [
        (119, '轻型自行火炮方案一：低突破、低成本、高软攻', 'Light SPG design 1: low breakthrough, low cost, high soft attack', 'complete'),
        (120, '轻型自行火炮方案二：约8造价、50软攻并可追加重机枪', 'Light SPG design 2: about 8 cost, 50 soft attack, with extra heavy machine guns', 'complete'),
    ]),
    ('tank_td', 505, 500, [
        (127, '先进高速加农炮坦歼完整设计：高穿深、高硬攻、固定炮台', 'Complete advanced high-velocity-cannon TD: high piercing and hard attack, fixed superstructure', 'complete'),
        (126, '改进型加农炮中型坦克参考；需点设计按钮切换为坦歼', 'Improved-cannon medium-tank reference; use the role button to convert it to a TD', 'reference'),
        (125, '改进高速加农炮中型坦克参考；当前角色仍是中型坦克', 'Improved high-velocity-cannon medium-tank reference; its current role is still Medium Tank', 'reference'),
    ]),
    ('tank_flame', 506, 500, [
        (129, '中型喷火坦克完整设计', 'Complete medium flame-tank design', 'complete'),
        (128, '装甲支援车生产列表：应选择自动退役的12造价型号', 'Armored support vehicle list: choose the auto-retired 12-cost model', 'partial'),
    ]),
    ('tank_mech', 507, 500, [
        (130, '机械化步兵前置步战车设计：5造价、2可靠', 'Mechanized-infantry prerequisite IFV: 5 cost and 2 reliability', 'complete'),
        (131, '假模板训练用低成本坦侦车设计', 'Low-cost armored recon vehicle for dummy-template training', 'complete'),
        (132, '一般作战用装甲侦察车设计', 'Armored recon vehicle for normal combat divisions', 'complete'),
    ]),
    ('plane_multirole', 601, 600, [
        (146, '火箭导轨解锁前的早期多功能设计', 'Early multirole design before rocket rails', 'complete'),
        (147, '火箭导轨解锁前的多功能方案', 'Pre-rocket-rail multirole configuration', 'complete'),
        (148, '中期至中后期火箭导轨多功能方案', 'Midwar and late-midwar rocket-rail multirole configuration', 'complete'),
    ]),
    ('plane_fighter', 602, 600, [
        (145, '纯种战斗机完整设计：本土防空与截击', 'Complete pure fighter for homeland defense and interception', 'complete'),
    ]),
    ('plane_cas', 603, 600, [
        (150, '近地支援机完整设计：夺取制空后堆航程与对地输出', 'Complete CAS design: stack range and ground attack after securing air superiority', 'complete'),
    ]),
    ('plane_equip', 604, 600, [
        (151, '同配件对照一：对地武器未放在首格', 'Identical-module comparison 1: ground weapon is not in the first slot', 'complete'),
        (152, '同配件对照二：对地武器放首格，可同时获得CAS与战斗机减价', 'Identical-module comparison 2: ground weapon first for both CAS and fighter discounts', 'complete'),
        (153, '1944年机体多功能完整设计', 'Complete 1944 multirole airframe design', 'complete'),
        (154, '后期二级机炮完整设计', 'Complete late-war level-2-cannon design', 'complete'),
        (149, '火箭导轨科技位置', 'Rocket-rail technology location', 'partial'),
    ]),
    ('ship_fleet', 701, 700, [
        (133, '36年满机库航母完整设计', 'Complete 1936 carrier with maximum hangars', 'complete'),
        (135, '为航母承伤的肉盾战列舰完整设计', 'Complete damage-soaking battleship for carrier screening', 'complete'),
    ]),
    ('ship_capital', 702, 700, [
        (134, '战列舰完整设计', 'Complete battleship design', 'complete'),
        (142, '战列舰与战巡舰的护甲差异', 'Battleship and battlecruiser armor comparison', 'partial'),
    ]),
    ('ship_cruiser', 703, 700, [
        (136, '避免交战的侦查轻巡完整设计', 'Complete Never Engage scout light cruiser', 'complete'),
        (137, '融化敌方屏卫的主力轻巡完整设计', 'Complete main-fleet light cruiser for destroying screens', 'complete'),
    ]),
    ('ship_dd', 704, 700, [
        (138, '维持屏卫效率的肉盾驱逐舰完整设计', 'Complete damage-soaking destroyer for screening efficiency', 'complete'),
        (141, '绿水学派鱼雷驱逐舰完整设计', 'Complete green-water torpedo destroyer', 'complete'),
    ]),
    ('ship_sub', 705, 700, [
        (139, '反潜方案一：用于保护舰队和航线，不是潜艇设计', 'ASW configuration 1 for protecting fleets and sea lanes; not a submarine design', 'context'),
        (140, '反潜方案二；舰载鱼雷机或海军轰炸机优先于反潜驱逐', 'ASW configuration 2; prefer carrier torpedo or naval bombers over ASW destroyers', 'context'),
    ]),
    ('ship_carair', 706, 700, [
        (143, '多功能舰攻：鱼雷/海军轰炸机，可攻击主力舰与潜艇', 'Multirole carrier torpedo/naval bomber for capital ships and submarines', 'complete'),
        (144, '舰爆：近地支援机方案，整体弱于多功能舰攻', 'Carrier dive/CAS bomber, generally weaker than the multirole torpedo bomber', 'complete'),
    ]),
]


def pages(name, event_id, menu, sources):
    for index, (media, caption_zh, caption_en, kind) in enumerate(sources, 1):
        yield {
            'name': name if index == 1 else f'{name}_page{index}',
            'id': event_id if index == 1 else event_id * 10 + index,
            'index': index,
            'total': len(sources),
            'media': media,
            'caption_zh': caption_zh,
            'caption_en': caption_en,
            'kind': kind,
            'menu': menu,
        }


# The tank menu previews the role-selection workflow, not an unrelated medium tank.
DESIGN_PICTURES = {'tank_menu': [116, 117, 118]}
for gallery in GALLERIES:
    for page in pages(*gallery):
        DESIGN_PICTURES[page['name']] = [page['media']]
