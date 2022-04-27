class SendMessageException(Exception):
    '''Исключине при отправки сообщения'''
    pass

class GetAPIException(Exception):
    '''Исключение при выполнении запроса'''
    pass

class CheckResponseException(Exception):
    '''Исключение при проверки запроса'''
    pass
