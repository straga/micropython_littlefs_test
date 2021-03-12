from mod.board._runner import BoardAction

_name = "board"
_schema = '''{
      "_sch_0": {
        "_schema" : "_schema",
        "name": "board_cfg",
        "sch": [
                  ["name", ["str",""] ],
                  ["board", ["str", ""] ],
                  ["hostname", ["str", ""]],
                  ["uid", ["str", ""]],
                  ["topic", ["str", ""]],
                  ["init",["int", 0]]
        ]
      }
    }'''

_action = BoardAction
_depend = []





