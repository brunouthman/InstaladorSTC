import cx_Oracle

class OracleConnect(object):
    def __init__(self):
        pass

    def validaUserOracle(self, usuario, senha):
        try:
            oracle_user_pwd = ('{}/{}@ORCL'.format(usuario, senha))
            con = cx_Oracle.connect(oracle_user_pwd)
            print (con.version)
            teste_retorno = con.version
            con.close()

            return teste_retorno
        except:
            return 'Erro'
