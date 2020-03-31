#!/usr/bin/env python3
from os import listdir
from config import LINK_ID
from datetime import datetime
from bs4 import BeautifulSoup
from os.path import isfile, join, exists


class TelegramMessage:
    def __init__(self, date: datetime, sender: str, senderid: int, userexist: bool, message: str, msgid: int):
        self.date = date
        self.sender = sender
        self.senderid = senderid
        self.userexist = userexist
        self.message = message
        self.msgid = msgid


def get_messages(message_files):
    objects = []
    UserGroup = []
    last_name = ""

    for message_file in message_files:
        with open(message_file, encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        default_messages = soup.select(".message.default")

        for mess in default_messages:
            textselection = mess.select_one(".text")
            dateselection = mess.select_one(".date")
            date = datetime.strptime(dateselection["title"], "%d.%m.%Y %H:%M:%S")
            msgid = int(mess["id"][7:])

            name = ""
            if "joined" in mess["class"]:
                name = last_name
            else:
                name = mess.select_one(".from_name").text.strip()
                last_name = name

            if textselection is not None:
                userexist = False
                _index = 0
                if name in UserGroup:
                    userexist = True
                    _index = UserGroup.index(name)
                else:
                    UserGroup.append(name)
                    _index = len(UserGroup) - 1
                obj = TelegramMessage(date, name, -_index, userexist, textselection.text.strip(), msgid)
                objects.append(obj)

    return objects


def insert_messages(messages):
    from database import DBSession, Message, User
    for message in messages:
        new_msg = Message(id=message.msgid, link='https://t.me/c/{}/{}'.format(LINK_ID, message.msgid), text=message.message, video='', photo='',
                          audio='', voice='', type='text', category='', from_id=message.senderid, date=message.date)
        session = DBSession()
        session.add(new_msg)
        if not message.userexist:
            new_user = User(id=message.senderid, fullname=message.sender, username='', update_time=datetime.now())
            session.add(new_user)
        session.commit()
        session.close()


def main():
    if exists('bot.db'):
        print('数据库已存在！')
        return

    exported_path = input('输入导出聊天记录路径：\n')
    message_files = [join(exported_path, f) for f in listdir(exported_path) if
                     isfile(join(exported_path, f)) and f.startswith('messages') and f.endswith('.html')]

    if not message_files:
        print('未发现聊天记录文件！')
        return
    print('发现聊天记录，检索中...')
    messages = get_messages(message_files)
    print('共{}条历史消息，导入中...'.format(len(messages)))
    insert_messages(messages)
    print('导入完成！')


if __name__ == "__main__":
    main()
