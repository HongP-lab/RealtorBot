"""Generates the Scenario A (text-only) blueprint for RealtorBot as scenario_a_blueprint.json."""
import json, os

HOOK_ID = int(os.environ.get("HOOK_ID", "2982961"))   # RealtorBot LINE webhook
LINE = 11951777          # RealtorBot Test (never 9081464)
CLAUDE = 9081069         # Claude Real Key
GOOGLE = 4480116         # Make academy
SHEET = "/1Pzh8td4QGDGjKPnCySNZMcBiuQfeJcml90STOrSjicg"

EV = "1.events[]"
USER = "{{" + EV + ".source.userId}}"
TEXT = "{{" + EV + ".message.text}}"
TOKEN = "{{" + EV + ".replyToken}}"
NOW = '{{formatDate(now; "YYYY-MM-DD HH:mm:ss"; "Asia/Bangkok")}}'
TODAY = '{{formatDate(now; "YYYY-MM-DD"; "Asia/Bangkok")}}'
STAMP = '{{formatDate(now; "YYMMDDHHmmss"; "Asia/Bangkok")}}'

PROMPT_A = (
    "คุณเป็นตัวแยกคำสั่งสำหรับนายหน้าอสังหาฯ ไทย ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่น ห้ามใส่ ```\n"
    "intent ที่เป็นไปได้: add_property, ask_price, search_property, update_client, set_followup, list_followups, unknown\n"
    "fields: intent, property_name, type (คอนโด/บ้าน/ทาวน์โฮม/ที่ดิน), area (ย่าน/ทำเล เป็นชื่อสถานที่ ไม่ใช่ตัวเลข), price (ตัวเลขบาท), "
    "sqm (ตัวเลข ตร.ม.), beds (ตัวเลขห้องนอน), transit (เช่น BTS หมอชิต), client_name, stage, "
    "followup_date (YYYY-MM-DD, ตีความ \"พรุ่งนี้/วันศุกร์\" จากวันนี้ = " + TODAY + "), note, question\n"
    "add_property ใช้ทั้งเพิ่มทรัพย์ใหม่ และเพิ่ม/แก้ข้อมูลทรัพย์เดิมที่ระบุชื่อ เช่น \"The Line Jatujak 120 ตร.ม.\" = add_property, sqm=120\n"
    "\"เพิ่มรูปทรัพย์ X\" หรือ \"รูปนี้ของ X\" = add_property, property_name=X (ระบบจะย้ายรูปที่เพิ่งส่งไปไว้ที่ทรัพย์นั้น)\n"
    "จำนวนห้องน้ำ หรือรายละเอียดอื่นที่ไม่มีฟิลด์ ให้ใส่ใน note เช่น \"3 ห้องน้ำ\"\n"
    "ผู้ใช้จะได้รับบทสนทนาล่าสุดมาด้วย ให้ใช้เติมสิ่งที่ผู้ใช้ไม่ได้พูดซ้ำ เช่น ชื่อทรัพย์ที่เพิ่งคุยกัน "
    "ถ้าข้อความล่าสุดเป็นคำตอบของคำถามที่ระบบเพิ่งถาม ให้รวมกับคำสั่งเดิมแล้วทำต่อ ไม่ต้องถามซ้ำ\n"
    "การเพิ่มข้อมูลให้ทรัพย์เดิมไม่จำเป็นต้องมีราคาหรือย่าน ขอแค่รู้ชื่อทรัพย์\n"
    "ถ้าผู้ใช้ระบุเลขห้อง/ยูนิต ให้รวมไว้ในชื่อทรัพย์รูปแบบ \"ชื่อโครงการ #เลขห้อง\" เช่น \"The Line Jatujak ห้อง 1204\" -> property_name=\"The Line Jatujak #1204\" "
    "ถ้าไม่ระบุเลขห้องให้ใช้ชื่อโครงการตามเดิม\n"
    "stage ต้องเป็นค่าใดค่าหนึ่ง: Inquiry, Viewing, Offer, Negotiation, Contract, Transfer (นัดดูห้อง = Viewing)\n"
    "ฟิลด์ที่ไม่มีให้ใส่ null\n"
    "ถ้าข้อมูลไม่ครบหรือไม่แน่ใจ ให้ intent=unknown และใส่ question ถามกลับสั้นๆ ห้ามเดาตัวเลข"
)

FALLBACK = "ขออภัยค่ะ ระบบขัดข้องชั่วคราว กรุณาลองส่งข้อความอีกครั้งในอีกสักครู่"
FIX_HINT = "\nถ้าผิด พิมพ์บอกใหม่ได้เลย เช่น \"แก้ ราคา 8900000\""


def reply(mid, text):
    return {"id": mid, "module": "line:sendAReplyMessage", "version": 1,
            "parameters": {"__IMTCONN__": LINE},
            "mapper": {"messages": [{"type": "text", "text": text}],
                       "replyToken": TOKEN, "notificationDisabled": False}}


def error_handler(base):
    if os.environ.get("DEBUG"):
        return []  # let errors surface in execution history
    return [reply(base, FALLBACK), {"id": base + 1, "module": "builtin:Ignore", "version": 1,
                                    "parameters": {}, "mapper": {}}]


def sheet_target(tab):
    return {"from": "drive", "mode": "select", "spreadsheetId": SHEET, "sheetId": tab,
            "includesHeaders": True}


def add_row(mid, tab, values, filt=None):
    m = {"id": mid, "module": "google-sheets:addRow", "version": 2,
         "parameters": {"__IMTCONN__": GOOGLE},
         "mapper": {**sheet_target(tab), "values": values, "insertUnformatted": False,
                    "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}}
    if filt:
        m["filter"] = filt
    return m


def update_row(mid, tab, row, values, filt=None):
    m = {"id": mid, "module": "google-sheets:updateRow", "version": 2,
         "parameters": {"__IMTCONN__": GOOGLE},
         "mapper": {**sheet_target(tab), "rowNumber": row, "values": values,
                    "valueInputOption": "RAW"}}
    if filt:
        m["filter"] = filt
    return m


def search(mid, tab, conditions, filt=None):
    m = {"id": mid, "module": "google-sheets:filterRows", "version": 2,
         "parameters": {"__IMTCONN__": GOOGLE, **sheet_target(tab), "tableFirstRow": "A1:Z1",
                        "valueRenderOption": "FORMATTED_VALUE",
                        "dateTimeRenderOption": "FORMATTED_STRING"},
         "mapper": {"filter": conditions, "sortOrder": "asc", "limit": "20"}}
    if filt:
        m["filter"] = filt
    return m


def text_agg(mid, feeder, value, sep="\n", filt=None):
    m = {"id": mid, "module": "util:TextAggregator", "version": 1,
         "parameters": {"feeder": feeder, "rowSeparator": sep},
         "mapper": {"value": value}}
    if filt:
        m["filter"] = filt
    return m


def when(cond, *parts):
    """Text that renders only when cond holds; parts are IML expressions (quote literals)."""
    return "".join("{{if(%s; %s; emptystring)}}" % (cond, p) for p in parts)


DRIVE = 11956360         # RealtorBot Drive 2 (google-drive type; the Sheets connection can't upload)
LINE_TOKEN = 11958488    # "LINE RealtorBot token" API-key credential, restricted to https://api-data.line.me
PHOTO_ROOT = "18YoyjRB3lvL0WwrGnkCxrQEv4I4ASsra"     # RealtorBot_Photos; each property gets a subfolder
PHOTO_FOLDER = "/" + PHOTO_ROOT
# Properties columns: 0 id, 5 area, 6 price, 7 sqm, 8 beds, 11 photo links, 13 photo_folder (Drive folder id)
DRAFT_FIELDS = [("U", 11), ("F", 13), ("I", 0)]                                # photos=2 folder=3 id=4
EXIST_FIELDS = [("U", 11), ("A", 5), ("P", 6), ("S", 7), ("B", 8), ("F", 13), ("I", 0)]  # photos=2 area..beds=3..6 folder=7 id=8


def row_agg(mid, feeder, fields):
    """One line per found row: <row>§<letter><value>..., the letters keep empty values in place
    so split() can't drop them; read values back with seg_row / seg_field."""
    parts = ["%d.`__ROW_NUMBER__`" % feeder]
    for letter, col in fields:
        parts += ['"§%s"' % letter, "%d.`%d`" % (feeder, col)]
    return text_agg(mid, feeder, when("length(%d.`0`) > 0" % feeder, *parts), sep="¶")


def seg_row(agg):
    return '{{first(split(first(split(%s.text; "¶")); "§"))}}' % agg


def seg_field(agg, pos):
    """Value at position pos (1-based) of the first row_agg line, without its letter prefix."""
    item = 'get(split(first(split(%s.text; "¶")); "§"); %d)' % (agg, pos)
    return 'substring(%s; 1; length(%s))' % (item, item)


draft_agg = lambda mid, feeder: row_agg(mid, feeder, DRAFT_FIELDS)
exist_agg = lambda mid, feeder: row_agg(mid, feeder, EXIST_FIELDS)
exist_field = seg_field


def upload(mid, folder, err_id, filt=None):
    m = {"id": mid, "module": "google-drive:uploadAFile", "version": 4,
         "parameters": {"__IMTCONN__": DRIVE},
         "mapper": {"destination": "drive", "folderId": folder, "data": "{{60.data}}",
                    # Drive appends the filename's extension to the title, so the title has none
                    "title": "{{" + EV + ".message.id}}", "filename": "{{" + EV + ".message.id}}.jpg",
                    "convert": False},
         "onerror": error_handler(err_id)}
    if filt:
        m["filter"] = filt
    return m


def drive_patch(mid, folder_expr, query, body, filt=None):
    """Rename/move a Drive folder via the Drive API (files.update)."""
    m = {"id": mid, "module": "google-drive:makeApiCall", "version": 4,
         "parameters": {"__IMTCONN__": DRIVE},
         "mapper": {"url": "/v3/files/{{" + folder_expr + "}}" + query, "method": "PATCH",
                    "headers": [{"key": "Content-Type", "value": "application/json"}],
                    "qs": [], "body": body}}
    if filt:
        m["filter"] = filt
    return m


def draft_search(mid, filt=None):
    return search(mid, "Properties", [[owner_eq("C"), {"a": "K", "o": "text:equal", "b": "draft"}]], filt)


PROPERTY_ID = '{{first(split(39.text; ","))}}'
INTEREST = '{{ifempty(first(split(39.text; ",")); "-")}}'


def intent_is(name, *intents):
    return {"name": name, "conditions": [[{"a": "{{3.intent}}", "o": "text:equal", "b": i}] for i in intents]}


owner_eq = lambda col: {"a": col, "o": "text:equal", "b": USER}

NOT_ARCHIVED = {"a": "K", "o": "text:notequal", "b": "archived"}
# Properties columns: 4 type, 5 area, 6 price, 7 sqm, 8 beds, 9 transit, 12 notes; empty values leave cells as they are
DETAILS = {"4": "{{3.type}}", "5": "{{3.area}}", "6": "{{3.price}}", "7": "{{3.sqm}}",
           "8": "{{3.beds}}", "9": "{{3.transit}}", "12": "{{3.note}}"}
DETAIL_SUMMARY = (' | ย่าน {{ifempty(3.area; "-")}} | ราคา {{ifempty(3.price; "-")}} บาท'
                  ' | {{ifempty(3.sqm; "-")}} ตร.ม. | {{ifempty(3.beds; "-")}} ห้องนอน')

EXIST_ROW = '{{first(split(first(split(76.text; "¶")); "§"))}}'
EXIST_PHOTOS = exist_field(76, 2)
# reply after updating an existing property: new value if given, else what the row already had
MERGED_SUMMARY = (' | ย่าน {{ifempty(3.area; ifempty(' + exist_field(76, 3) + '; "-"))}}'
                  ' | ราคา {{ifempty(3.price; ifempty(' + exist_field(76, 4) + '; "-"))}} บาท'
                  ' | {{ifempty(3.sqm; ifempty(' + exist_field(76, 5) + '; "-"))}} ตร.ม.'
                  ' | {{ifempty(3.beds; ifempty(' + exist_field(76, 6) + '; "-"))}} ห้องนอน')
EXIST_FOLDER = seg_field(76, 7)
DRAFT_ROW_71, DRAFT_PHOTOS_71, DRAFT_FOLDER_71, DRAFT_ID_71 = seg_row(71), seg_field(71, 2), seg_field(71, 3), seg_field(71, 4)
DRAFT_ROW_63, DRAFT_PHOTOS_63, DRAFT_FOLDER_63 = seg_row(63), seg_field(63, 2), seg_field(63, 3)
photo_link = lambda mod: "https://drive.google.com/file/d/{{%d.id}}/view" % mod
# existing links + new link, space-separated
PHOTOS_AFTER = "{{" + DRAFT_PHOTOS_63 + "}}{{if(length(" + DRAFT_PHOTOS_63 + ') > 0; " "; emptystring)}}' + photo_link(81)
NO_DRAFT_63 = {"name": "no draft yet", "conditions": [[{"a": "{{63.text}}", "o": "notexist"}]]}
HAS_DRAFT_63 = {"name": "append to draft", "conditions": [[{"a": "{{63.text}}", "o": "exist"}]]}

image_route = [
    # LINE image content expires, so download and store it right away
    # LINE's own modules only reach api.line.me (405/404); image content lives on api-data.line.me,
    # so download it over HTTP with the channel token kept in a Make API-key credential
    {"id": 60, "module": "http:DownloadFile", "version": 4,
     # field names as saved by the Make UI ("apiKey" is the legacy keychain type)
     "parameters": {"authenticationType": "apiKeyConnection", "apiKeyAccount": LINE_TOKEN},
     "filter": {"name": "LINE image message", "conditions": [[
         {"a": "{{" + EV + ".type}}", "o": "text:equal", "b": "message"},
         {"a": "{{" + EV + ".message.type}}", "o": "text:equal", "b": "image"}]]},
     "mapper": {"url": "https://api-data.line.me/v2/bot/message/{{" + EV + ".message.id}}/content",
                "shareCookies": False, "stopOnHttpError": True},
     "onerror": error_handler(94)},
    draft_search(64),
    draft_agg(63, 64),
    {"id": 65, "module": "builtin:BasicRouter", "version": 1, "mapper": None, "routes": [
        # first photo: new draft folder inside RealtorBot_Photos, renamed once the property is named
        {"flow": [
            {"id": 80, "module": "google-drive:createAFolder", "version": 4,
             "parameters": {"__IMTCONN__": DRIVE}, "filter": NO_DRAFT_63,
             "mapper": {"destination": "drive", "folderId": PHOTO_FOLDER,
                        "name": 'draft {{formatDate(now; "YYYY-MM-DD HH:mm"; "Asia/Bangkok")}}'}},
            upload(61, "/{{80.id}}", 96),
            add_row(62, "Log", {"0": NOW, "1": USER, "2": "[image]", "3": "image", "4": photo_link(61), "5": "received"}),
            add_row(66, "Properties", {"0": "P-" + STAMP, "1": NOW, "2": USER, "10": "draft",
                                       "11": photo_link(61), "13": "{{80.id}}"}),
            reply(67, 'รับรูปแล้ว (1 รูป) ส่งรูปเพิ่มได้ หรือพิมพ์รายละเอียดทรัพย์ต่อได้เลย เช่น "เพิ่มทรัพย์ Lumière ย่านอโศก ราคา 8900000"'),
        ]},
        # more photos: into the draft's folder (older drafts without one fall back to the root)
        {"flow": [
            upload(81, '/{{ifempty(' + DRAFT_FOLDER_63 + '; "' + PHOTO_ROOT + '")}}', 98, HAS_DRAFT_63),
            add_row(82, "Log", {"0": NOW, "1": USER, "2": "[image]", "3": "image", "4": photo_link(81), "5": "received"}),
            update_row(68, "Properties", DRAFT_ROW_63, {"11": PHOTOS_AFTER}),
            reply(69, 'รับรูปแล้ว ({{length(split(trim(' + DRAFT_PHOTOS_63 + '); " ")) + 1}} รูป) ส่งรูปเพิ่มได้ หรือพิมพ์รายละเอียดทรัพย์ต่อได้เลย'),
        ]},
    ]},
]

flow = [
    {"id": 1, "module": "gateway:CustomWebHook", "version": 1,
     "parameters": {"hook": HOOK_ID, "maxResults": 1}, "mapper": {}},
    # Claude has no memory between messages: feed it this user's latest Log rows as context
    {**search(7, "Log", [[{"a": "B", "o": "text:equal", "b": USER}]],
              {"name": "LINE text message only", "conditions": [[
                  {"a": "{{" + EV + ".type}}", "o": "text:equal", "b": "message"},
                  {"a": "{{" + EV + ".message.type}}", "o": "text:equal", "b": "text"}]]}),
     "mapper": {"filter": [[{"a": "B", "o": "text:equal", "b": USER}]],
                "sortOrder": "desc", "orderBy": "A", "limit": "6"}},
    text_agg(8, 7, when("length(7.`2`) > 0", "newline", '"- ผู้ใช้: "', "7.`2`",
                        '" | ระบบเข้าใจเป็น: "', "7.`4`"), sep=" "),
    {"id": 2, "module": "anthropic-claude:createAMessage", "version": 1,
     "parameters": {"__IMTCONN__": CLAUDE},
     "mapper": {"model": "claude-haiku-4-5-20251001", "system": PROMPT_A,
                "messages": [{"role": "user", "inputType": "single",
                              "content": "บทสนทนาล่าสุด (ใหม่สุดอยู่บน):{{ifempty(8.text; \" ไม่มี\")}}\n\nข้อความใหม่: " + TEXT}],
                "metadata": {}, "thinking": {"type": "disabled"}, "container": {},
                # numbers, not strings: the API rejects "400" with a 400 error
                "max_tokens": 400, "temperature": 0, "tool_choice": {},
                "outputFormat": {"type": "text"}},
     "onerror": error_handler(90)},
    {"id": 3, "module": "json:ParseJSON", "version": 1, "parameters": {},
     "mapper": {"json": '{{trim(replace(replace(2.textResponse; "```json"; emptystring); "```"; emptystring))}}'},
     "onerror": error_handler(92)},
    add_row(4, "Log", {"0": NOW, "1": USER, "2": TEXT, "3": "{{3.intent}}",
                       "4": "{{2.textResponse}}", "5": "received"}),
    {"id": 5, "module": "builtin:BasicRouter", "version": 1, "mapper": None, "routes": [
        # add_property: same name -> update that row; else fill the photo draft; else add a new row
        {"flow": [
            search(75, "Properties", [[owner_eq("C"), NOT_ARCHIVED,
                                       {"a": "D", "o": "text:equal:ci", "b": '{{ifempty(3.property_name; "§none§")}}'}]],
                   intent_is("add_property", "add_property")),
            exist_agg(76, 75),
            draft_search(70),
            draft_agg(71, 70),
            {"id": 72, "module": "builtin:BasicRouter", "version": 1, "mapper": None, "routes": [
                {"flow": [
                    update_row(77, "Properties", EXIST_ROW, {
                        **DETAILS,
                        # always write back the row's own photos (an empty value clears the cell), plus any draft photos
                        "11": "{{" + EXIST_PHOTOS + "}}"
                              "{{if(length(71.text) > 0; if(length(" + EXIST_PHOTOS + ") > 0; \" \"; emptystring); emptystring)}}"
                              "{{if(length(71.text) > 0; " + DRAFT_PHOTOS_71 + "; emptystring)}}",
                        # keep the property's own folder; adopt the draft's if it had none
                        "13": "{{if(length(71.text) > 0; ifempty(" + EXIST_FOLDER + "; " + DRAFT_FOLDER_71 + "); " + EXIST_FOLDER + ")}}"},
                        {"name": "same name exists", "conditions": [[{"a": "{{76.text}}", "o": "exist"}]]}),
                    reply(79, 'อัปเดตทรัพย์เดิมแล้ว: {{3.property_name}}' + MERGED_SUMMARY + FIX_HINT),
                    update_row(78, "Properties", DRAFT_ROW_71, {"10": "archived"},
                               {"name": "had a draft", "conditions": [[{"a": "{{71.text}}", "o": "exist"}]]}),
                    # draft folder: moved inside the property's folder, or renamed to become it
                    drive_patch(83, DRAFT_FOLDER_71,
                                '{{if(length(' + EXIST_FOLDER + ') > 0; "?addParents="; emptystring)}}'
                                '{{if(length(' + EXIST_FOLDER + ') > 0; ' + EXIST_FOLDER + '; emptystring)}}'
                                '{{if(length(' + EXIST_FOLDER + ') > 0; "&removeParents=' + PHOTO_ROOT + '"; emptystring)}}',
                                '{"name": "{{if(length(' + EXIST_FOLDER + ') > 0; "รูปเพิ่ม "; emptystring)}}'
                                '{{if(length(' + EXIST_FOLDER + ') > 0; formatDate(now; "YYYY-MM-DD HH:mm"; "Asia/Bangkok"); emptystring)}}'
                                '{{if(length(' + EXIST_FOLDER + ') = 0; ' + seg_field(76, 8) + '; emptystring)}}'
                                '{{if(length(' + EXIST_FOLDER + ') = 0; " "; emptystring)}}'
                                '{{if(length(' + EXIST_FOLDER + ') = 0; 3.property_name; emptystring)}}"}',
                                {"name": "draft has a folder", "conditions": [[
                                    {"a": "{{" + DRAFT_FOLDER_71 + "}}", "o": "exist"}]]}),
                ]},
                {"flow": [
                    update_row(73, "Properties", DRAFT_ROW_71, {
                        **DETAILS, "1": NOW, "3": "{{3.property_name}}", "10": "active"},
                        {"name": "new name, has draft", "conditions": [[
                            {"a": "{{76.text}}", "o": "notexist"}, {"a": "{{71.text}}", "o": "exist"}]]}),
                    reply(74, 'บันทึกแล้ว: {{3.property_name}}' + DETAIL_SUMMARY + ' | รูป {{length(split(trim(' + DRAFT_PHOTOS_71 + '); " "))}} รูป' + FIX_HINT),
                    drive_patch(84, DRAFT_FOLDER_71, "",
                                '{"name": "{{' + DRAFT_ID_71 + '}} {{3.property_name}}"}',
                                {"name": "draft has a folder", "conditions": [[
                                    {"a": "{{" + DRAFT_FOLDER_71 + "}}", "o": "exist"}]]}),
                ]},
                {"flow": [
                    add_row(10, "Properties", {
                        **DETAILS, "0": "P-" + STAMP, "1": NOW, "2": USER, "3": "{{3.property_name}}", "10": "active"},
                        {"name": "new name, no draft", "conditions": [[
                            {"a": "{{76.text}}", "o": "notexist"}, {"a": "{{71.text}}", "o": "notexist"}]]}),
                    reply(11, 'บันทึกแล้ว: {{3.property_name}}' + DETAIL_SUMMARY + FIX_HINT),
                ]},
            ]},
        ]},
        # ask_price / search_property — answers come only from the sheet
        {"flow": [
            search(20, "Properties", [
                [owner_eq("C"), NOT_ARCHIVED, {"a": "D", "o": "text:contain:ci", "b": '{{ifempty(3.property_name; "§none§")}}'}],
                [owner_eq("C"), NOT_ARCHIVED, {"a": "F", "o": "text:contain:ci", "b": '{{ifempty(3.area; "§none§")}}'}]],
                intent_is("ask_price / search_property", "ask_price", "search_property")),
            # the search can hand the aggregator an empty bundle, so each line is built only for real rows
            text_agg(21, 20, when("length(20.`3`) > 0", "newline", '"• "', "20.`3`", '" ("', "20.`5`",
                                  '") ราคา "', "20.`6`", '" บาท | สถานะ "', "20.`10`"), sep=" "),
            reply(22, '{{ifempty(trim(21.text); "ไม่พบทรัพย์ที่ตรงกับคำค้นในข้อมูลของคุณ")}}'),
        ]},
        # update_client / set_followup
        {"flow": [
            search(30, "Clients", [[owner_eq("B"), {"a": "C", "o": "text:contain:ci",
                                                     "b": '{{ifempty(3.client_name; "§none§")}}'}]],
                   intent_is("update_client / set_followup", "update_client", "set_followup")),
            text_agg(31, 30, when("length(30.`2`) > 0", "30.`__ROW_NUMBER__`"), sep=","),
            # look up the property the client is interested in (own rows only); empty when none named
            search(38, "Properties", [[owner_eq("C"), NOT_ARCHIVED, {"a": "D", "o": "text:contain:ci",
                                                        "b": '{{ifempty(3.property_name; "§none§")}}'}]]),
            text_agg(39, 38, when("length(38.`3`) > 0", "38.`0`"), sep=","),
            {"id": 32, "module": "builtin:BasicRouter", "version": 1, "mapper": None, "routes": [
                {"flow": [
                    add_row(33, "Clients", {
                        "0": "C-" + STAMP, "1": USER, "2": "{{3.client_name}}", "3": "",
                        "4": PROPERTY_ID, "5": '{{ifempty(3.stage; "Inquiry")}}', "6": "{{3.followup_date}}",
                        "7": "{{3.note}}", "8": NOW},
                        {"name": "new client", "conditions": [[{"a": "{{31.text}}", "o": "notexist"}]]}),
                    reply(34, 'บันทึกแล้ว (ลูกค้าใหม่): {{3.client_name}} | stage {{ifempty(3.stage; "Inquiry")}} | follow-up {{ifempty(3.followup_date; "-")}} | สนใจ ' + INTEREST + FIX_HINT),
                ]},
                {"flow": [
                    update_row(35, "Clients", '{{first(split(31.text; ","))}}', {
                        "4": PROPERTY_ID, "5": "{{3.stage}}", "6": "{{3.followup_date}}", "7": "{{3.note}}", "8": NOW},
                        {"name": "exactly one match", "conditions": [[
                            {"a": "{{31.text}}", "o": "exist"},
                            {"a": '{{length(split(31.text; ","))}}', "o": "number:equal", "b": "1"}]]}),
                    reply(36, 'บันทึกแล้ว: {{3.client_name}} | stage {{ifempty(3.stage; "ไม่เปลี่ยน")}} | follow-up {{ifempty(3.followup_date; "ไม่เปลี่ยน")}} | สนใจ ' + INTEREST + FIX_HINT),
                ]},
                {"flow": [
                    # router runs every route whose filter passes; without this filter it replied twice
                    {**reply(37, 'พบลูกค้าชื่อ "{{3.client_name}}" มากกว่า 1 คน กรุณาพิมพ์ชื่อเต็มให้ชัดขึ้นค่ะ'),
                     "filter": {"name": "more than one match", "conditions": [[
                         {"a": "{{31.text}}", "o": "exist"},
                         {"a": '{{length(split(31.text; ","))}}', "o": "number:greater", "b": "1"}]]}},
                ]},
            ]},
        ]},
        # list_followups
        {"flow": [
            search(40, "Clients", [[owner_eq("B")]], intent_is("list_followups", "list_followups")),
            # filters in front of an aggregator never let rows through in testing, so the
            # "due today or earlier" check lives inside the line; YYYYMMDD compares correctly as text
            text_agg(41, 40, when('replace(ifempty(40.`6`; "99999999"); "-"; emptystring) <= formatDate(now; "YYYYMMDD"; "Asia/Bangkok")',
                                  "newline", '"• "', "40.`2`", '" — "', "40.`5`", '" (นัด "', "40.`6`", '") "', "40.`7`"),
                     sep=" "),
            reply(42, '{{ifempty(trim(41.text); "วันนี้ไม่มีลูกค้าที่ต้อง follow up ค่ะ")}}'),
        ]},
        # unknown / anything else
        {"flow": [
            reply(50, '{{ifempty(3.question; "ขอโทษค่ะ ยังไม่เข้าใจคำสั่ง ลองพิมพ์ เช่น ‘Lumière ราคาเท่าไร’ หรือ ‘ใครต้อง follow up วันนี้’")}}'),
        ]},
    ]},
]
# give the unknown route a filter: intent is unknown or missing
intent_router = next(m for m in flow if m["id"] == 5)
intent_router["routes"][4]["flow"][0]["filter"] = {"name": "unknown", "conditions": [
    [{"a": "{{3.intent}}", "o": "text:equal", "b": "unknown"}],
    [{"a": "{{3.intent}}", "o": "notexist"}]]}

# top-level split: text goes through Claude, images go straight to Drive
flow = [flow[0], {"id": 6, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
                  "routes": [{"flow": flow[1:]}, {"flow": image_route}]}]

blueprint = {"name": "RealtorBot - Scenario A (text)", "flow": flow,
             "metadata": {"version": 1, "instant": True,
                          # sequential: a burst of photos must see each other's draft row, not race
                          "scenario": {"roundtrips": 1, "maxErrors": 3, "autoCommit": True,
                                       "sequential": True, "dataloss": False, "dlq": False}}}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario_a_blueprint.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(blueprint, f, ensure_ascii=False, indent=1)
print(out)
