# -*- coding: utf-8 -*-
from tkinter import *
import os
import sys
import subprocess

class Application:
    def __init__(self, master=None):
        self.fontePadrao = ("Arial", "10")
        self.primeiroContainer = Frame(master)
        self.primeiroContainer["padx"] = 50
        self.primeiroContainer.pack()

        self.segundoContainer = Frame(master)
        self.segundoContainer["padx"] = 50
        self.segundoContainer.pack()

        self.terceiroContainer = Frame(master)
        self.terceiroContainer["padx"] = 50
        self.terceiroContainer.pack()

        self.quartoContainer = Frame(master)
        self.quartoContainer["padx"] = 50
        self.quartoContainer.pack()

        self.titulo = Label(self.primeiroContainer, text="Instalador STC")
        self.titulo["font"] = ("Arial", "16", "bold")
        self.titulo.pack(side=RIGHT)

        self.pergunta = Label(self.segundoContainer, text="Instalar STC?")
        self.pergunta["font"] = ("Arial", "10")
        self.pergunta.pack()

        self.botaoInstalar = Button(self.terceiroContainer)
        self.botaoInstalar["text"] = "Sim"
        self.botaoInstalar["font"] = ("Calibri", "8")
        self.botaoInstalar["width"] = 12
        self.botaoInstalar["command"] = self.instalarSTC
        self.botaoInstalar.pack(side=LEFT)

        self.botaoInstalar = Button(self.terceiroContainer)
        self.botaoInstalar["text"] = "Nao"
        self.botaoInstalar["font"] = ("Calibri", "8")
        self.botaoInstalar["width"] = 12
        self.botaoInstalar["command"] = self.sairInstalador
        self.botaoInstalar.pack()

        self.mensagem = Label(self.quartoContainer, text="", font=self.fontePadrao)
        self.mensagem.pack(side=LEFT)

    # Metodo verificar senha
    def instalarSTC(self):
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
            print('Erro - "c:\STC\Client\ConfigSTC.ini" nao encontrado!!!')
            os.system("pause")
            sys.exit()

        start = "C:\\STC\\Server"

        for dirpath, dirnames, filenames in os.walk(start):
            for filename in filenames:
                if filename == "ConfigSTC.ini":
                    erro = "N"
                    filename = os.path.join(dirpath, filename)
                    print(filename)
                    print(dirpath)

        if  erro == "S":
            print('Erro - "c:\STC\Server\ConfigSTC.ini" nao encontrado!!!')
            os.system("pause")
            sys.exit()

#############################################
########## validar ORACLE ###################
#############################################

######Validando se funciona o tnsping

        proc = subprocess.Popen(["tnsping", "ORCL"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        pos_ini = out.find(b'C:\\')
        pos_fin = out.find(b'sqlnet.ora')
        pos_falha = out.find(b'Falha')

        if  (pos_ini or pos_fin) > 0:       #####   aqui trocar por simbolo de menor(<)
            print('Oracle não instalado, por favor verifique!!!')
            os.system("pause")
            sys.exit()
        else:
            # caminho = " "

############# caminho = (out[pos_ini:pos_fin])    >>>> aqui esta o caminho
#######>>>>>> excluir depois
            caminho = 'C:\\app\\bruno.uthman\\product\\11.2.0\\client_1\\network\\admin'
#######>>>>>> excluir depois os comments

            if  pos_falha > 0:
                print('configurar o tnsname ORCL em: {}'.format(caminho))
                os.system('{}\\tnsnames.ora'.format(caminho))
                os.system("pause")
                sys.exit()
            else:
                print('Oracle ok')


######## configurando o tnsname ORCL
########## >>>>>precisa fazer depois


        print('ENDDDDD!!!!!!')
        os.system("pause")
        sys.exit()





    def sairInstalador(self):
        sys.exit()


root = Tk()
root.geometry('{}x{}'.format(500, 150))
Application(root)
root.mainloop()