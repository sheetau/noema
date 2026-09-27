"""Author the reviewed 0.3 additions; never used by natural-language inference."""
import json
from pathlib import Path

NOUNS = [
    ("person", "人", "A human person; identity, age and social role are unspecified."),
    ("water", "水", "Liquid water as a substance or a designated portion; a count does not imply a volume unit."),
    ("food", "食べ物", "Material designated for eating; composition and serving size are unspecified."),
    ("bread", "パン", "Bread as food; a count refers to explicitly individuated portions, not an inferred mass."),
    ("fruit", "果物", "An edible fruit; species is unspecified."),
    ("cup", "カップ", "A small open vessel used for drinking; contents are not implied."),
    ("bottle", "瓶", "A container with a narrow opening; material and contents are unspecified."),
    ("table", "机・テーブル", "A piece of furniture with a raised working or supporting surface."),
    ("chair", "椅子", "A seat intended for one person."),
    ("door", "扉", "A movable barrier controlling passage through an opening."),
    ("window", "窓", "An opening in a building or vehicle for light or viewing, with or without glazing."),
    ("bag", "鞄", "A flexible container intended for carrying objects."),
    ("key", "鍵", "A physical object intended to operate a lock; not an abstract solution or keyboard key."),
    ("pen", "ペン", "A handheld instrument that writes with ink."),
    ("paper", "紙", "Paper material or explicitly individuated sheets; a count does not imply sheet dimensions."),
    ("message", "メッセージ", "An individuated communicative item; content is not inferred from its name."),
    ("computer", "コンピューター", "A programmable computing device."),
    ("phone", "電話機", "A device intended for remote voice communication; not the act of calling."),
    ("vehicle", "乗り物", "A conveyance for people or goods; propulsion and mode are unspecified."),
    ("bicycle", "自転車", "A pedal-driven two-wheeled vehicle."),
    ("tree", "木", "An individual woody plant with a substantial persistent stem."),
    ("flower", "花", "An individual blossom, meaning the reproductive flowering structure of a plant; not the whole plant."),
    ("clothing", "衣服", "An individuated item of clothing; type and wearer are unspecified."),
    ("tool", "道具", "An implement used to perform a task; the task is not inferred."),
]
PLACES = [
    ("place", "場所", "A designated spatial location; extent and type are unspecified."),
    ("room", "部屋", "An interior space separated as a room."),
    ("school", "学校", "A location used for organized teaching; not the institution as a legal person."),
    ("shop", "店", "A location used for retail exchange."),
    ("station", "駅", "A location where public transport regularly stops for passengers."),
    ("road", "道路", "A route prepared or customarily used for travel."),
    ("city", "都市", "A settlement designated as a city; no population threshold is implied."),
    ("garden", "庭", "An area cultivated for plants or outdoor use."),
    ("workplace", "仕事場", "A location at which work is performed; employer and occupation are unspecified."),
]
EVENTS = [
    ("eat", "食べる", "agent consumes patient as food", "agent patient location instrument"),
    ("drink", "飲む", "agent takes patient liquid into the body by drinking", "agent patient location instrument"),
    ("read", "読む", "agent interprets written content presented by patient", "agent patient location"),
    ("write", "書く", "agent inscribes or composes patient as written material", "agent patient recipient location instrument"),
    ("move", "移動する", "agent changes spatial position from source to destination; either endpoint may be unspecified", "agent source destination location"),
    ("carry", "運ぶ", "agent transports patient from source to destination", "agent patient source destination location instrument beneficiary"),
    ("arrive", "到着する", "agent reaches destination; departure location may be specified as source", "agent source destination location"),
    ("leave", "出発する", "agent departs source; destination may be unspecified", "agent source destination location"),
    ("wait", "待つ", "agent remains pending patient; the duration is unspecified", "agent patient location"),
    ("work", "働く", "agent performs work; occupation and outcome are unspecified", "agent location instrument beneficiary"),
    ("learn", "学ぶ", "agent acquires knowledge or skill represented by patient", "agent patient location"),
    ("teach", "教える", "agent provides instruction about patient to recipient", "agent patient recipient location"),
    ("meet", "会う", "agent encounters patient; prior acquaintance is unspecified", "agent patient location"),
    ("speak", "話す", "agent produces spoken communication about patient for recipient", "agent patient recipient location"),
    ("hear", "聞こえる", "agent auditorily perceives patient; intentional listening is not implied", "agent patient location"),
    ("buy", "買う", "agent obtains patient in exchange for payment; price is unspecified", "agent patient location beneficiary"),
    ("sell", "売る", "agent transfers patient to recipient in exchange for payment; price is unspecified", "agent patient recipient location"),
    ("make", "作る", "agent brings patient into existence or produces it", "agent patient location instrument beneficiary"),
    ("use", "使う", "agent employs patient for an unspecified purpose", "agent patient location"),
    ("open_action", "開ける", "agent changes patient to an open state", "agent patient location instrument"),
    ("close_action", "閉める", "agent changes patient to a closed state", "agent patient location instrument"),
    ("find", "見つける", "agent comes to locate or discover patient", "agent patient location"),
    ("send", "送る", "agent dispatches patient toward recipient or destination; receipt is not asserted", "agent patient recipient source destination location instrument"),
    ("receive", "受け取る", "agent takes delivery of patient; the sender is unspecified", "agent patient location"),
    ("wash", "洗う", "agent cleans patient using liquid", "agent patient location instrument"),
]
STATES = [
    ("present_at", "そこにある・いる", "agent is spatially present at location", "agent location"),
    ("have", "所持する", "agent possesses patient; legal ownership is not asserted", "agent patient location"),
    ("contain", "含む", "agent contains patient spatially or as a component", "agent patient location"),
    ("like", "好む", "agent has a favorable preference toward patient", "agent patient location"),
    ("need", "必要とする", "agent requires patient; fulfillment is not asserted", "agent patient location"),
    ("know", "知っている", "agent is acquainted with patient; proposition knowledge is not encoded", "agent patient location"),
    ("tired", "疲れている", "agent experiences fatigue", "agent location"),
    ("happy", "うれしい", "agent experiences happiness", "agent location"),
    ("red", "赤い", "agent has a red appearance under contextually relevant viewing conditions", "agent location"),
    ("blue", "青い", "agent has a blue appearance under contextually relevant viewing conditions", "agent location"),
    ("large", "大きい", "agent is large relative to an unspecified contextual comparison class", "agent location"),
    ("small", "小さい", "agent is small relative to an unspecified contextual comparison class", "agent location"),
    ("open_state", "開いている", "agent is in an open configuration; an opening event is not asserted", "agent location"),
    ("closed_state", "閉じている", "agent is in a closed configuration; a closing event is not asserted", "agent location"),
    ("wet", "濡れている", "agent has liquid on or absorbed into its surface", "agent location"),
    ("dry", "乾いている", "agent lacks relevant surface moisture relative to context", "agent location"),
    ("hot", "熱い", "agent has a high temperature relative to context; no degree value is specified", "agent location"),
    ("cold", "冷たい", "agent has a low temperature relative to context; no degree value is specified", "agent location"),
]


def build():
    alphabet = "abcdefghijklmnopqrstuvwxyz234567"
    concepts, roots = {}, {}
    for prefix, word_prefix, kind, entries in [("c", "ma", "entity", NOUNS), ("d", "la", "place", PLACES), ("e", "va", "event", EVENTS), ("f", "sa", "state", STATES)]:
        for index, row in enumerate(entries):
            label, ja, definition, *roles = row
            ident = prefix + alphabet[index]
            concepts[ident] = {"kind": kind, "label": label, "ja": ja, "definition": definition + ("." if not definition.endswith(".") else "")}
            if roles:
                concepts[ident]["roles"] = roles[0].split()
                concepts[ident]["role_types"] = {r: ["place"] if r in ("location", "source", "destination") else ["entity", "place"] if label in ("present_at", "contain", "red", "blue", "large", "small", "open_state", "closed_state", "wet", "dry", "hot", "cold") and r == "agent" else ["entity"] for r in roles[0].split()}
            roots[ident] = word_prefix + alphabet[index]
    return {"version": "0.3", "status": "development", "extends": "0.2", "roots": roots, "concepts": concepts,
            "inherited_ja": dict(zip(("aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai", "ba", "bb", "bc", "bd", "be", "bf"),
                                     ("犬", "猫", "子供", "先生", "鳥", "本", "名前で指定する人物", "公園", "家", "追う", "見る", "助ける", "渡す", "眠る", "空腹である"))),
            "role_markers": {"z": "source", "2": "destination", "3": "instrument", "4": "beneficiary"}}


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "noema/resources/language-v03.json"
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
