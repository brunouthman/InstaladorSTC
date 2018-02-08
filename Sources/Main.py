# -*- coding: utf-8 -*-
from tkinter import *
import os
import sys
import subprocess
from subprocess import STDOUT, check_output
from OracleConnect import OracleConnect
from pymsgbox import *

class Application:
    def __init__(self, master=None):
        self.montaTela(master)

    def instalarSTC(self):
        self.validaUserOracle()

        self.validaSTC()

        self.validaOracleTNSNAME()

        self.sairInstalador()

    def validaUserOracle(self):
        text = 'Atenção: a instalação apagará todos os dados das tabelas!'
        alert(text=text, title="Instalador STC", button='OK')

        usuario = self.usuario.get()
        senha = self.senha.get()

        if (usuario != "system") and (usuario != "SYSTEM"):
            self.mensagem["text"] = "Usuario Invalido!!!"
            root.mainloop()

        if senha == "":
            self.mensagem["text"] = "Senha Invalida!!!"
            root.mainloop()

        teste_retorno = OracleConnect.validaUserOracle(self, usuario, senha)

        pos_erro = teste_retorno.find('Erro')
        pos_falha = teste_retorno.find('Falha')
        pos_ora12154 = teste_retorno.find('ORA-12154')

    #######DESCOMENTAR APOS TESTES
    #    if  (pos_falha or pos_ora12154) >= 0:
    #        self.mensagem["text"] = "Senha Invalida!!!"
    #        root.mainloop()

    #    if  pos_erro >= 0:
    #        self.mensagem["text"] = "Erro no acesso ao Oracle, verifique!"
    #        root.mainloop()


    def validaSTC(self):
        print('Validando STC...')

######## matando os processos STC
        os.system('tskill STCLauncher')
        os.system('tskill STCDIS')
        os.system('tskill STCPanel')
        os.system('tskill STCPlayback')
        os.system('tskill STCInterfaceExterna')
        os.system('tskill STCMQ')
        os.system('tskill STCMQMonitor')
        os.system('tskill HybridOBCSimulator')
        os.system('tskill Decryptor')
        os.system('tskill Encryptor')


######## matando os servicos STC
        os.system('net stop ABR')
        os.system('net stop STC.Router.Service')
        os.system('net stop STCGlobal')

######## exclui STC_old
        os.system('rd c:\STC_old /s/q')

######## STC antigo para STC_old
        os.system('move c:\STC c:\STC_old')

########## copia STC novo pasta para c:\
        os.system('mkdir c:\STC')

        dirname = os.path.dirname(os.path.realpath(sys.argv[0]))
        caminho = ('xcopy {}\STC\*.* c:\STC /E '.format(dirname))
        os.system(caminho)

#######Validar.pasta_stc()
        start = "C:\\STC\\Client"

        erro = "S"

        for dirpath, dirnames, filenames in os.walk(start):
            for filename in filenames:
                if filename == "ConfigSTC.ini":
                    erro = "N"
                    filename = os.path.join(dirpath, filename)
                    print(filename)
                    print(dirpath)

        if  erro == "S":
            self.mensagem["text"] = 'Erro - "c:\STC\Client\ConfigSTC.ini" nao encontrado!!!'
            root.mainloop()

        start = "C:\\STC\\Server"

        for dirpath, dirnames, filenames in os.walk(start):
            for filename in filenames:
                if filename == "ConfigSTC.ini":
                    erro = "N"
                    filename = os.path.join(dirpath, filename)
                    print(filename)
                    print(dirpath)

        if  erro == "S":
            self.mensagem["text"] = 'Erro - "c:\STC\Server\ConfigSTC.ini" nao encontrado!!!'
            root.mainloop()

    def validaOracleTNSNAME(self):
######Validando se funciona o tnsping

        proc = subprocess.Popen(["tnsping", "ORCL"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        pos_ini = out.find(b'C:\\')
        pos_fin = out.find(b'sqlnet.ora')
        pos_falha = out.find(b'Falha')
        pos_erro = out.find(b'erro')

        if  (pos_ini or pos_fin) > 0:       #####   aqui trocar por simbolo de menor(<)
            self.mensagem["text"] = 'Oracle não instalado, por favor verifique!!!'
            root.mainloop()

        if  pos_erro >= 0:
            self.mensagem["text"] = 'Oracle não instalado, por favor verifique!!!'
            root.mainloop()


    #   caminho = " "

########caminho = (out[pos_ini:pos_fin])    >>>> aqui esta o caminho
#######>> excluir depois
        caminho = 'C:\\app\\bruno.uthman\\product\\11.2.0\\client_1\\network\\admin'
#######>> excluir depois os comments

        if  pos_falha >= 0:
            alert(text="Configurar TNSNAME ORCL!!!", title="Instalador STC", button='OK')
            os.system('{}\\tnsnames.ora'.format(caminho))
            self.mensagem["text"] = 'logar novamente...'
            root.mainloop()


        print('Oracle ok')
        proc.kill()

######### start no listner

        proc = subprocess.Popen(["lsnrctl", "start"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        print(out)

        pos_comando_interno = out.find(b'comando interno')
        pos_erro = out.find(b'erro')
        pos_falha = out.find(b'Falha')

        if  (pos_comando_interno or pos_erro or pos_falha) >= 0:
            self.mensagem["text"] = 'Erro no start listener Oracle, verifique!!!'
            root.mainloop()


        print('Listener ok')
        proc.kill()



        print('ENDDDDD!!!!!!')
        os.system("pause")
        sys.exit()

    def montaTela(self, master):
        self.fontePadrao = ("Arial", "10")
        self.primeiroContainer = Frame(master)
        self.primeiroContainer["pady"] = 10
        self.primeiroContainer.pack()

        self.segundoContainer = Frame(master)
        self.segundoContainer["padx"] = 20
        self.segundoContainer.pack()

        self.terceiroContainer = Frame(master)
        self.terceiroContainer["padx"] = 20
        self.terceiroContainer.pack()

        self.quartoContainer = Frame(master)
        self.quartoContainer["padx"] = 20
        self.quartoContainer.pack()

        self.quintoContainer = Frame(master)
        self.quintoContainer["padx"] = 20
        self.quintoContainer.pack()

        self.sextoContainer = Frame(master)
        self.sextoContainer["pady"] = 20
        self.sextoContainer.pack()

        self.setimoContainer = Frame(master)
        self.setimoContainer["padx"] = 20
        self.setimoContainer.pack()

        self.titulo = Label(self.primeiroContainer, text="Instalador STC")
        self.titulo["font"] = ("Arial", "15", "bold")
        self.titulo.pack()

        self.titulo = Label(self.segundoContainer, text="Informe usuario system@ORCL do Oracle")
        self.titulo["font"] = ("Arial", "10")
        self.titulo.pack()

        self.usuarioLabel = Label(self.terceiroContainer, text="Usuario", font=self.fontePadrao)
        self.usuarioLabel.pack(side=LEFT)

        self.usuario = Entry(self.terceiroContainer)
        self.usuario["width"] = 30
        self.usuario["font"] = self.fontePadrao
        self.usuario.pack(side=LEFT)

        self.senhaLabel = Label(self.quartoContainer, text="Senha", font=self.fontePadrao)
        self.senhaLabel.pack(side=LEFT)

        self.senha = Entry(self.quartoContainer)
        self.senha["width"] = 30
        self.senha["font"] = self.fontePadrao
        self.senha["show"] = "*"
        self.senha.pack(side=LEFT)

        self.instalar = Button(self.quintoContainer)
        self.instalar["text"] = "Instalar"
        self.instalar["font"] = ("Calibri", "8")
        self.instalar["width"] = 12
        self.instalar["command"] = self.instalarSTC
        self.instalar.pack(side=LEFT)

        self.instalar = Button(self.quintoContainer)
        self.instalar["text"] = "Sair"
        self.instalar["font"] = ("Calibri", "8")
        self.instalar["width"] = 12
        self.instalar["command"] = self.sairInstalador
        self.instalar.pack(side=LEFT)

        self.mensagem = Label(self.sextoContainer, text="", font=self.fontePadrao)
        self.mensagem.pack(side=LEFT)

        aviso = 'Atenção: a instalação apagará todos os dados das tabelas!'
        self.aviso = Label(self.setimoContainer, text=aviso, font=self.fontePadrao)
        self.aviso.pack(side=LEFT)



    def sairInstalador(self):
        sys.exit()




root = Tk()
Application(root)
root.mainloop()