import configparser
import inspect

config = None

class MyError():

  def __init__(self, et):
    self.config = configparser.RawConfigParser()
    self.config.read('ErrorMessages.properties')
    self.errorType = et

  def newError(self, showKey, key, linha=None, coluna=None, **data):
    
    message = ''
    message = f"Erro[{linha}][{coluna}]: "
    if(showKey):
      return(key)
    else:  
      if(key):
        if(linha == None or coluna == None):
          message = self.config.get(self.errorType, key)
        else:
          message += self.config.get(self.errorType, key)
      if(data):
        for key, value in data.items():
          message = message + ", " f"{key}: {value}"

    
      return(message)
    
      #frame = inspect.stack()[1][0]

      #print(inspect.getframeinfo(frame).__getitem__(0))
      #print(inspect.getframeinfo(frame).__getitem__(1))


# le = MyError('LexerErrors')

# print(le.newError('ERR-LEX-001'))
