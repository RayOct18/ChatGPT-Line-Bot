
def help(*arg, **kwargs):
    return {
  "type": "carousel",
  "contents": [
    {
      "type": "bubble",
      "size": "micro",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "常用指令",
            "color": "#ffffff",
            "align": "center",
            "size": "md",
            "gravity": "center"
          }
        ],
        "backgroundColor": "#27ACB2",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "文字轉語音",
                "color": "#6FB7B7",
                "size": "sm",
                "wrap": True,
                "align": "center",
                "decoration": "underline",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/文字轉語音"
                }
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "清除所有聊天記錄",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/清除所有聊天記錄"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "所有指令說明",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/所有指令說明"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "目前語音",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/目前語音"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": False
        }
      }
    },
    {
      "type": "bubble",
      "size": "micro",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "系統相關",
            "color": "#ffffff",
            "align": "center",
            "size": "md",
            "gravity": "center"
          }
        ],
        "backgroundColor": "#46A3FF",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "目前使用金鑰",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/目前使用金鑰"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "目前系統訊息",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/目前系統訊息"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "目前記憶聊天筆數",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/目前記憶聊天筆數"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "目前聊天紀錄",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/目前聊天紀錄"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": False
        }
      }
    },
    {
      "type": "bubble",
      "size": "micro",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "color": "#ffffff",
            "align": "center",
            "size": "md",
            "gravity": "center",
            "text": "."
          }
        ],
        "backgroundColor": "#46A3FF",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "目前快捷關鍵字",
                "color": "#6FB7B7",
                "size": "sm",
                "wrap": True,
                "align": "center",
                "decoration": "underline",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/目前快捷關鍵字"
                }
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "清除所有快捷關鍵字",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/清除所有快捷關鍵字"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": False
        }
      }
    },
    {
      "type": "bubble",
      "size": "micro",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "設定指令",
            "color": "#ffffff",
            "align": "center",
            "size": "md",
            "gravity": "center"
          }
        ],
        "backgroundColor": "#C48888",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "註冊OpenAI",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/註冊OpenAI help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "註冊ElevenLabs",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/註冊ElevenLabs help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "設定記憶數量",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/設定記憶數量 help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "設定系統訊息",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/設定系統訊息 help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": False
        }
      }
    },
    {
      "type": "bubble",
      "size": "micro",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": ".",
            "color": "#ffffff",
            "align": "center",
            "size": "md",
            "gravity": "center"
          }
        ],
        "backgroundColor": "#C48888",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "新增關鍵字",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/新增關鍵字 help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "刪除關鍵字",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/刪除關鍵字 help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "設定語音",
                "action": {
                  "type": "message",
                  "label": "action",
                  "text": "/設定語音 help"
                },
                "wrap": True,
                "size": "sm",
                "color": "#6FB7B7",
                "decoration": "underline",
                "align": "center"
              }
            ]
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": False
        }
      }
    }
  ]
}