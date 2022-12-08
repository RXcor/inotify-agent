from watchdog.events import EVENT_TYPE_CREATED,\
    EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED,\
    EVENT_TYPE_CLOSED


def singleton(class_):
    instances = {}
    def get_instances(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return get_instances


@singleton
class MessagesBufer:
    '''
    Буфер сообщений для уменьшения количества 
    однотипных сообщений от файловой системы
    '''
    def __init__(self):
        # создаем 4 очереди, чтобы удаление не отправить перед созданием
        # пример сообщения: {('path', 'name'): json_message}
        self.cr_messages = {} # создание
        self.upd_messages = {} # обновление
        self.clwr_messages = {} # выход с записью
        self.del_messages = {} # удаление
        # Такая структура позволит удалить самые старые однотипные сообщения.
        # Например два сообщения типа update для одного файла поданные на вход будут записаны как одно - самое новое
        self.caches_bind = {
            EVENT_TYPE_CREATED: self.cr_messages,
            EVENT_TYPE_CLOSED: self.clwr_messages,
            EVENT_TYPE_MODIFIED: self.upd_messages,
            EVENT_TYPE_DELETED: self.del_messages 
        }
    
    def send_mes_to_buf(self, event_type, path, name, json_message) -> None:

        buf = self.caches_bind[event_type]
        buf[(path, name)] = json_message

    def pop_all_messages_by_event_type(self, event_type):
        buf = self.caches_bind[event_type]
        curent_keys = [* buf.keys()]
        return list([ buf.pop(key) for key in curent_keys])
    
