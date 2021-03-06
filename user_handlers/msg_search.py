# coding: utf-8
import math
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
from config import SEARCH_PAGE_SIZE, GROUP_ID
from database import User, Message, DBSession
import re


def search_messages(keyword, page):
    messages = []
    start = (page - 1) * SEARCH_PAGE_SIZE
    stop = page * SEARCH_PAGE_SIZE
    session = DBSession()
    if keyword:
        count = session.query(Message).filter(Message.text.ilike('%{}%'.format(keyword))).count()
        query = session.query(Message).filter(Message.text.ilike('%{}%'.format(keyword))).order_by(
            Message.date.desc()).slice(start, stop)
    else:
        count = session.query(Message).count()
        query = session.query(Message).filter().order_by(Message.date.desc()).slice(start, stop)
    for message in query.all():
        user = session.query(User).filter_by(id=message.from_id).one()
        user_fullname = user.fullname
        if message.type != 'text':
            msg_text = '[{}]'.format(message.type)
        else:
            msg_text = message.text
        messages.append(
            {'id': message.id, 'link': message.link, 'text': msg_text, 'date': message.date, 'user': user_fullname,
             'type': message.type})

    session.close()
    return messages, count


def inline_caps(bot, update):
    from_user_id = update.inline_query.from_user.id
    # 检查是否为群成员
    try:
        StatGroup =['left', 'kicked', 'none']
        flag = bot.get_chat_member(chat_id=GROUP_ID, user_id=from_user_id).status
        for stat in StatGroup:
            if flag == stat:
                return        
    except:
        return

    query = update.inline_query.query
    # recent messages
    if not query: 
        keyword, page = None, 1

    elif re.match(r' *\* +(\d+)', query):
        keyword, page = None, int(re.match(r'\* +(\d+)', query).group(1))
    # search messages
    else:
        re_match = re.match(r'(.*) +(\d+)', query)
        if re_match:
            keyword, page = re_match.group(1), int(re_match.group(2))
        else:
            keyword, page = query, 1
    messages, count = search_messages(keyword, page)
    results = [InlineQueryResultArticle(
        id='info',
        title='Total:{}. Page {} of {}'.format(count, page, math.ceil(count / SEARCH_PAGE_SIZE)),
        input_message_content=InputTextMessageContent('/help')
    )]
    for message in messages:
        msg = ((message['text'].replace('"', '&quot;', len(message['text']))).replace('<', '&lt;', len(message['text']))).replace('>', '&gt;', len(message['text']))
        user = ((message['user'].replace('"', '&quot;', len(message['user']))).replace('<', '&lt;', len(message['user']))).replace('>', '&gt;', len(message['user']))
        text = '<i>{}</i><a href="{}">「From {}」</a>'.format(msg, message['link'], user)
        results.append(
            InlineQueryResultArticle(
                id=message['id'],
                title='{}'.format(message['text'][:100]),
                description=message['date'].strftime("%Y-%m-%d").ljust(40) + message['user'],
                input_message_content=InputTextMessageContent(text, parse_mode='HTML'))
            )
    bot.answer_inline_query(update.inline_query.id, results)


handler = InlineQueryHandler(inline_caps)
