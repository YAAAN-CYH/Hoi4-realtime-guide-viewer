"""Ship mapping. Word aircraft, tank and army chapters have separate owners."""

# name, base event ID, chapter menu,
# (PPT media ID, Chinese caption, English caption, semantic image kind).
# A reference is a complete screenshot whose on-screen role must be converted
# before it becomes the finished design discussed by the surrounding topic.
GALLERIES = [
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


DESIGN_PICTURES = {}
for gallery in GALLERIES:
    for page in pages(*gallery):
        DESIGN_PICTURES[page['name']] = [page['media']]
