import random
import unicodedata

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput


class SquareGrid(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)

    def do_layout(self, *args):
        if self.parent:
            side = min(self.parent.width, self.parent.height)
            if self.width != side or self.height != side:
                self.size = (side, side)
        super().do_layout(*args)


class ButtonVivo(Button):
    def __init__(self, **kwargs):
        super().__init__(background_normal='', **kwargs)


class BotaoMenu(ButtonBehavior, BoxLayout):
    def __init__(self, c_imagem, texto, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = dp(10)
        self.spacing = dp(15)

        self.icone = Image(
            source=c_imagem,
            size_hint=(None, 1),
            width=self.height,
            fit_mode='contain',
            allow_stretch=True
        )
        self.bind(height=self._atualizar_largura_icone)
        self.add_widget(self.icone)

        self.label = Label(
            text=texto,
            font_size=sp(20),
            bold=True,
            halign='left',
            valign='middle',
            size_hint=(1, 1)
        )
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

    def _atualizar_largura_icone(self, instance, value):
        self.icone.width = max(dp(10), value - dp(20))


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))

        btn_batalha = BotaoMenu(
            c_imagem='icone_batalha.png',
            texto="BATALHA NAVAL"
        )
        btn_batalha.bind(on_release=lambda x: setattr(self.manager, 'current', 'batalha_naval'))
        layout.add_widget(btn_batalha)

        btn_forca = BotaoMenu(
            c_imagem='icone_forca.png',
            texto="FORCA"
        )
        btn_forca.bind(on_release=lambda x: setattr(self.manager, 'current', 'jogo_da_forca'))
        layout.add_widget(btn_forca)

        btn_velha = BotaoMenu(
            c_imagem='icone_velha.png',
            texto="JOGO DA VELHA"
        )
        btn_velha.bind(on_release=lambda x: setattr(self.manager, 'current', 'jogo_da_velha'))
        layout.add_widget(btn_velha)

        self.add_widget(layout)


class BatalhaNavalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tamanho_tabuleiro = 10
        self.navios_para_posicionar = [2, 2, 2, 3, 3, 4]

        self.cores_navios = [
            (1.0, 0.4, 0.7, 1.0),
            (1.0, 0.5, 0.0, 1.0),
            (0.5, 0.0, 0.5, 1.0),
            (0.5, 0.25, 0.0, 1.0),
            (0.5, 0.5, 0.5, 1.0),
            (0.85, 0.65, 0.35, 1.0)
        ]

        self.jogadores = {
            1: {"nome": "JOGADOR 1", "navios": [], "tiros_recebidos": {}},
            2: {"nome": "JOGADOR 2", "navios": [], "tiros_recebidos": {}}
        }

        self.jogador_atual = 1
        self.idx_navio_atual = 0
        self.coords_em_selecao = []
        self.fase = "NOMES"
        self.posicionamento_concluido = False
        self.aguardando_confirmacao_tiro = False
        self.evento_piscar_vitoria = None
        self.evento_piscar_afundados = None
        self.estado_piscar_afundados = False

        self.root_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(self.root_layout)

    def on_enter(self):
        self.reiniciar_jogo()

    def get_hex_cor_jogador(self, p_num):
        return "00FF00" if p_num == 1 else "FFFF00"

    def get_rgba_cor_jogador(self, p_num):
        return (0, 1, 0, 1) if p_num == 1 else (1, 1, 0, 1)

    def criar_botao_voltar_topo(self):
        btn_voltar = Button(text="< VOLTAR AO MENU PRINCIPAL", size_hint_y=0.08, font_size=sp(14))
        btn_voltar.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        return btn_voltar

    def forcar_maiusculas(self, instance, value):
        instance.text = value.upper()

    def mostrar_tela_nomes(self):
        self.limpar_eventos_piscar()
        self.root_layout.clear_widgets()

        self.root_layout.add_widget(self.criar_botao_voltar_topo())

        box_conteudo = BoxLayout(orientation='vertical', spacing=dp(10), size_hint=(1, 0.92))

        titulo = Label(
            text="BATALHA NAVAL", color=(1, 1, 1, 1), font_size=sp(26), bold=True,
            size_hint_y=0.15
        )
        box_conteudo.add_widget(titulo)

        lbl_j1 = Label(
            text="NOME DO JOGADOR 1 (VERDE):", color=(0, 1, 0, 1), font_size=sp(16), bold=True,
            size_hint_y=0.1
        )
        self.input_j1 = TextInput(
            text=self.jogadores[1]["nome"], multiline=False, font_size=sp(22), halign='center',
            size_hint_y=0.15
        )
        self.input_j1.bind(text=self.forcar_maiusculas)

        lbl_j2 = Label(
            text="NOME DO JOGADOR 2 (AMARELO):", color=(1, 1, 0, 1), font_size=sp(16), bold=True,
            size_hint_y=0.1
        )
        self.input_j2 = TextInput(
            text=self.jogadores[2]["nome"], multiline=False, font_size=sp(22), halign='center',
            size_hint_y=0.15
        )
        self.input_j2.bind(text=self.forcar_maiusculas)

        box_conteudo.add_widget(lbl_j1)
        box_conteudo.add_widget(self.input_j1)
        box_conteudo.add_widget(lbl_j2)
        box_conteudo.add_widget(self.input_j2)

        btn_iniciar = Button(
            text="CONFIRMAR E CONTINUAR",
            size_hint_y=0.25, font_size=sp(20), bold=True
        )
        btn_iniciar.bind(on_press=self.salvar_nomes)
        box_conteudo.add_widget(btn_iniciar)

        self.root_layout.add_widget(box_conteudo)

    def salvar_nomes(self, instance):
        nome1 = self.input_j1.text.strip().upper() or "JOGADOR 1"
        nome2 = self.input_j2.text.strip().upper() or "JOGADOR 2"
        self.jogadores[1]["nome"] = nome1
        self.jogadores[2]["nome"] = nome2

        self.fase = "POSICIONAMENTO"
        self.jogador_atual = 1
        self.idx_navio_atual = 0
        self.coords_em_selecao = []
        self.mostrar_tela_posicionamento()

    def mostrar_tela_posicionamento(self):
        self.limpar_eventos_piscar()
        self.root_layout.clear_widgets()
        self.posicionamento_concluido = False

        self.root_layout.add_widget(self.criar_botao_voltar_topo())

        hex_cor = self.get_hex_cor_jogador(self.jogador_atual)
        cor_rgba = self.get_rgba_cor_jogador(self.jogador_atual)
        cor_texto_btn = (0, 0, 0, 1) if self.jogador_atual == 2 else (1, 1, 1, 1)
        nome_p = self.jogadores[self.jogador_atual]["nome"]
        tam_navio = self.navios_para_posicionar[self.idx_navio_atual]

        self.status_label = Label(
            text=f"[color={hex_cor}]{nome_p}\nPOSICIONE O BARCO DE TAMANHO {tam_navio}[/color]",
            font_size=sp(15), size_hint_y=0.09, halign="center", markup=True, bold=True
        )
        self.root_layout.add_widget(self.status_label)

        self.topo_posicionamento_container = BoxLayout(size_hint_y=0.07)
        self.btn_topo_posicionamento = ButtonVivo(
            text="POSICIONAR ALEATORIAMENTE", color=cor_texto_btn, background_color=cor_rgba, font_size=sp(13), bold=True
        )
        self.btn_topo_posicionamento.bind(on_press=self.acao_botao_topo_posicionamento)
        self.topo_posicionamento_container.add_widget(self.btn_topo_posicionamento)
        self.root_layout.add_widget(self.topo_posicionamento_container)

        anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.68)
        grid = SquareGrid(cols=10, rows=10, spacing=dp(2))
        self.grid_botoes = {}

        for r in range(10):
            for c in range(10):
                btn = ButtonVivo(text="", font_size=sp(12), bold=True)
                btn.pos_coord = (r, c)
                btn.bind(on_press=self.tentar_posicionar_quadrante)
                grid.add_widget(btn)
                self.grid_botoes[(r, c)] = btn

        anchor.add_widget(grid)
        self.atualizar_visualizacao_posicionamento()
        self.root_layout.add_widget(anchor)

        btn_reiniciar = Button(text="REINICIAR JOGO", size_hint_y=0.08, font_size=sp(14))
        btn_reiniciar.bind(on_press=self.reiniciar_jogo)
        self.root_layout.add_widget(btn_reiniciar)

    def acao_botao_topo_posicionamento(self, instance):
        if self.posicionamento_concluido:
            self.avancar_apos_posicionamento()
        else:
            self.posicionar_aleatorio()

    def tentar_posicionar_quadrante(self, instance):
        if self.posicionamento_concluido:
            return

        r, c = instance.pos_coord
        coord = (r, c)

        navios_atuais = self.jogadores[self.jogador_atual]["navios"]
        coords_salvas = [c_pos for n in navios_atuais for c_pos in n["coords"]]
        if coord in coords_salvas:
            return

        hex_cor = self.get_hex_cor_jogador(self.jogador_atual)
        nome_p = self.jogadores[self.jogador_atual]["nome"]

        if coord in self.coords_em_selecao:
            self.coords_em_selecao.remove(coord)
            tam_navio = self.navios_para_posicionar[self.idx_navio_atual]
            faltam = tam_navio - len(self.coords_em_selecao)
            self.status_label.text = f"[color={hex_cor}]{nome_p}\nSELECIONE {faltam} QUADRANTE(S) PARA O BARCO DE TAMANHO {tam_navio}[/color]"
            self.atualizar_visualizacao_posicionamento()
            return

        if self.coords_em_selecao:
            adjacente = False
            for cr, cc in self.coords_em_selecao:
                if (abs(cr - r) == 1 and cc == c) or (abs(cc - c) == 1 and cr == r):
                    adjacente = True
                    break
            if not adjacente:
                return

            linhas = {pos[0] for pos in self.coords_em_selecao} | {r}
            colunas = {pos[1] for pos in self.coords_em_selecao} | {c}
            if len(linhas) > 1 and len(colunas) > 1:
                return

        self.coords_em_selecao.append(coord)
        tam_necessario = self.navios_para_posicionar[self.idx_navio_atual]

        if len(self.coords_em_selecao) == tam_necessario:
            navios_atuais.append({"coords": list(self.coords_em_selecao), "afundado": False})
            self.coords_em_selecao.clear()
            self.idx_navio_atual += 1

            if self.idx_navio_atual >= len(self.navios_para_posicionar):
                self.marcar_posicionamento_concluido()
                return

        tam_navio = self.navios_para_posicionar[self.idx_navio_atual]
        faltam = tam_navio - len(self.coords_em_selecao)
        self.status_label.text = f"[color={hex_cor}]{nome_p}\nSELECIONE {faltam} QUADRANTE(S) PARA O BARCO DE TAMANHO {tam_navio}[/color]"
        self.atualizar_visualizacao_posicionamento()

    def posicionar_aleatorio(self, instance=None):
        self.coords_em_selecao.clear()
        navios_atuais = self.jogadores[self.jogador_atual]["navios"]
        coords_ocupadas = {c for n in navios_atuais for c in n["coords"]}

        while self.idx_navio_atual < len(self.navios_para_posicionar):
            tam = self.navios_para_posicionar[self.idx_navio_atual]
            posicionado = False
            tentativas = 0
            while not posicionado and tentativas < 1000:
                tentativas += 1
                orientacao = random.choice(["H", "V"])
                if orientacao == "H":
                    r = random.randint(0, 9)
                    c = random.randint(0, 10 - tam)
                    coords_propostas = [(r, c + i) for i in range(tam)]
                else:
                    r = random.randint(0, 10 - tam)
                    c = random.randint(0, 9)
                    coords_propostas = [(r + i, c) for i in range(tam)]

                if not any(cp in coords_ocupadas for cp in coords_propostas):
                    navios_atuais.append({"coords": coords_propostas, "afundado": False})
                    coords_ocupadas.update(coords_propostas)
                    self.idx_navio_atual += 1
                    posicionado = True

        self.marcar_posicionamento_concluido()

    def marcar_posicionamento_concluido(self):
        self.posicionamento_concluido = True
        self.atualizar_visualizacao_posicionamento()
        hex_cor = self.get_hex_cor_jogador(self.jogador_atual)
        nome_p = self.jogadores[self.jogador_atual]["nome"]
        self.status_label.text = f"[color={hex_cor}]{nome_p}\nTODOS OS BARCOS FORAM POSICIONADOS![/color]"

        self.btn_topo_posicionamento.text = "CONCLUÍDO! CLIQUE PARA CONTINUAR"
        self.btn_topo_posicionamento.background_color = self.get_rgba_cor_jogador(self.jogador_atual)
        self.btn_topo_posicionamento.color = (0, 0, 0, 1) if self.jogador_atual == 2 else (1, 1, 1, 1)

    def atualizar_visualizacao_posicionamento(self):
        navios = self.jogadores[self.jogador_atual]["navios"]

        coords_com_cor = {}
        for idx, n in enumerate(navios):
            cor = self.cores_navios[idx % len(self.cores_navios)]
            for coord in n["coords"]:
                coords_com_cor[coord] = cor

        for coord, btn in self.grid_botoes.items():
            btn.color = (1, 1, 1, 1)
            if coord in coords_com_cor:
                btn.background_color = coords_com_cor[coord]
                btn.text = "X"
            elif coord in self.coords_em_selecao:
                cor_selecao = self.cores_navios[self.idx_navio_atual % len(self.cores_navios)]
                btn.background_color = cor_selecao
                btn.text = "+"
            else:
                btn.background_color = (0, 0.6, 1, 1)
                btn.text = ""

    def avancar_apos_posicionamento(self):
        if self.jogador_atual == 1:
            self.jogador_atual = 2
            self.idx_navio_atual = 0
            self.mostrar_tela_posicionamento()
        else:
            self.jogador_atual = 1
            self.iniciar_fase_ataque()

    def iniciar_fase_ataque(self):
        self.fase = "ATAQUE"
        self.aguardando_confirmacao_tiro = False
        self.limpar_eventos_piscar()
        self.root_layout.clear_widgets()

        oponente = 2 if self.jogador_atual == 1 else 1
        hex_cor = self.get_hex_cor_jogador(self.jogador_atual)
        nome_ataca = self.jogadores[self.jogador_atual]["nome"]

        self.root_layout.add_widget(self.criar_botao_voltar_topo())

        self.topo_container = BoxLayout(orientation='vertical', size_hint_y=0.12)
        self.status_label = Label(
            text=f"[color={hex_cor}]JOGADOR DA VEZ: {nome_ataca}\nFAÇA SEU DISPARO[/color]",
            font_size=sp(17), halign="center", markup=True, bold=True
        )
        self.topo_container.add_widget(self.status_label)
        self.root_layout.add_widget(self.topo_container)

        anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.72)
        grid = SquareGrid(cols=10, rows=10, spacing=dp(2))
        self.grid_botoes = {}
        tiros_existentes = self.jogadores[oponente]["tiros_recebidos"]

        for r in range(10):
            for c in range(10):
                btn = ButtonVivo(text="", font_size=sp(14), bold=True)
                btn.pos_coord = (r, c)

                if (r, c) in tiros_existentes:
                    resultado = tiros_existentes[(r, c)]
                    if resultado == "ACERTO":
                        btn.text = "X"
                        btn.color = (1, 1, 1, 1)
                        btn.background_color = (0, 1, 0, 1)
                    else:
                        btn.text = "O"
                        btn.color = (1, 1, 1, 1)
                        btn.background_color = (1, 0, 0, 1)
                else:
                    btn.background_color = (0, 0.6, 1, 1)
                    btn.bind(on_press=self.processar_disparo)

                grid.add_widget(btn)
                self.grid_botoes[(r, c)] = btn

        anchor.add_widget(grid)
        self.root_layout.add_widget(anchor)

        btn_reiniciar = Button(text="REINICIAR JOGO", size_hint_y=0.08, font_size=sp(14))
        btn_reiniciar.bind(on_press=self.reiniciar_jogo)
        self.root_layout.add_widget(btn_reiniciar)

        self.verificar_e_aplicar_cores_navios_afundados(oponente)
        self.evento_piscar_afundados = Clock.schedule_interval(
            lambda dt: self.alternar_piscar_afundados(oponente), 1.0 / 3.0
        )

    def processar_disparo(self, instance):
        if self.fase != "ATAQUE" or self.aguardando_confirmacao_tiro:
            return

        coord = instance.pos_coord
        oponente = 2 if self.jogador_atual == 1 else 1
        navios_oponente = self.jogadores[oponente]["navios"]
        tiros_oponente = self.jogadores[oponente]["tiros_recebidos"]
        todas_coords_navios = [c for n in navios_oponente for c in n["coords"]]

        acertou = coord in todas_coords_navios

        if acertou:
            tiros_oponente[coord] = "ACERTO"
            instance.text = "X"
            instance.color = (1, 1, 1, 1)
            instance.background_color = (0, 1, 0, 1)
            afundou_agora = self.verificar_e_aplicar_cores_navios_afundados(oponente)
        else:
            tiros_oponente[coord] = "AGUA"
            instance.text = "O"
            instance.color = (1, 1, 1, 1)
            instance.background_color = (1, 0, 0, 1)
            afundou_agora = False

        instance.unbind(on_press=self.processar_disparo)

        total_quadrantes_navios = len(todas_coords_navios)
        acertos_totais = sum(1 for v in tiros_oponente.values() if v == "ACERTO")

        if acertos_totais == total_quadrantes_navios:
            self.fase = "FIM"
            self.evento_piscar_vitoria = Clock.schedule_interval(self.piscar_vencedor, 0.25)
        else:
            self.aguardando_confirmacao_tiro = True
            self.exibir_botao_confirmacao_disparo(oponente, acertou, afundou_agora)

    def exibir_botao_confirmacao_disparo(self, oponente, acertou, afundou):
        self.topo_container.clear_widgets()

        if afundou:
            texto = "VOCÊ AFUNDOU UM BARCO!\nCLIQUE PARA CONTINUAR"
            cor_bg = (0, 1, 0, 1)
        elif acertou:
            texto = "VOCÊ ACERTOU UMA EMBARCAÇÃO!\nCLIQUE PARA CONTINUAR"
            cor_bg = (0, 1, 0, 1)
        else:
            texto = "VOCÊ ATIROU NA ÁGUA!\nCLIQUE PARA CONTINUAR"
            cor_bg = (1, 0, 0, 1)

        btn_continuar = ButtonVivo(
            text=texto, background_color=cor_bg, color=(1, 1, 1, 1), font_size=sp(14), bold=True, halign="center"
        )
        btn_continuar.bind(on_press=lambda inst: self.confirmar_continuar_turno(oponente))
        self.topo_container.add_widget(btn_continuar)

    def confirmar_continuar_turno(self, oponente):
        self.jogador_atual = oponente
        self.iniciar_fase_ataque()

    def verificar_e_aplicar_cores_navios_afundados(self, oponente):
        navios = self.jogadores[oponente]["navios"]
        tiros = self.jogadores[oponente]["tiros_recebidos"]
        houve_novo_afundamento = False

        for idx, navio in enumerate(navios):
            afundou = all(c in tiros and tiros[c] == "ACERTO" for c in navio["coords"])
            if afundou:
                if not navio["afundado"]:
                    navio["afundado"] = True
                    houve_novo_afundamento = True

        return houve_novo_afundamento

    def alternar_piscar_afundados(self, oponente):
        self.estado_piscar_afundados = not self.estado_piscar_afundados
        navios = self.jogadores[oponente]["navios"]

        for idx, navio in enumerate(navios):
            if navio.get("afundado", False):
                cor_afundado = self.cores_navios[idx % len(self.cores_navios)]

                for c in navio["coords"]:
                    if c in self.grid_botoes:
                        btn = self.grid_botoes[c]
                        btn.color = (1, 1, 1, 1)
                        if self.estado_piscar_afundados:
                            btn.background_color = cor_afundado
                            btn.text = "X"
                        else:
                            btn.background_color = (0, 0.6, 1, 1)
                            btn.text = ""

    def piscar_vencedor(self, dt):
        hex_vencedor = self.get_hex_cor_jogador(self.jogador_atual)
        nome_vencedor = self.jogadores[self.jogador_atual]["nome"]
        self.status_label.text = f"[color={hex_vencedor}]VENCEDOR: {nome_vencedor}[/color]"
        self.status_label.opacity = 0 if self.status_label.opacity == 1 else 1

    def limpar_eventos_piscar(self):
        if self.evento_piscar_vitoria:
            self.evento_piscar_vitoria.cancel()
            self.evento_piscar_vitoria = None
        if self.evento_piscar_afundados:
            self.evento_piscar_afundados.cancel()
            self.evento_piscar_afundados = None

    def reiniciar_jogo(self, instance=None):
        self.limpar_eventos_piscar()
        self.jogadores = {
            1: {"nome": "JOGADOR 1", "navios": [], "tiros_recebidos": {}},
            2: {"nome": "JOGADOR 2", "navios": [], "tiros_recebidos": {}}
        }
        self.jogador_atual = 1
        self.idx_navio_atual = 0
        self.coords_em_selecao.clear()
        self.mostrar_tela_nomes()


class JogoDaVelhaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.simbolo_atual = "X"
        self.vencedor = None
        self.botoes = []
        self.evento_piscar = None
        self.botoes_vencedores = []

        self.jogadores = {
            "X": "JOGADOR 1",
            "O": "JOGADOR 2"
        }

        self.root_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(self.root_layout)

    def on_enter(self):
        self.reiniciar_jogo()

    def criar_botao_voltar_topo(self):
        btn_voltar = Button(text="< VOLTAR AO MENU PRINCIPAL", size_hint_y=0.08, font_size=sp(14))
        btn_voltar.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        return btn_voltar

    def forcar_maiusculas(self, instance, value):
        instance.text = value.upper()

    def mostrar_tela_nomes(self):
        if self.evento_piscar:
            self.evento_piscar.cancel()
            self.evento_piscar = None

        self.root_layout.clear_widgets()

        self.root_layout.add_widget(self.criar_botao_voltar_topo())

        box_conteudo = BoxLayout(orientation='vertical', spacing=dp(10), size_hint=(1, 0.92))

        titulo = Label(
            text="JOGO DA VELHA", color=(1, 1, 1, 1), font_size=sp(26), bold=True,
            size_hint_y=0.15
        )
        box_conteudo.add_widget(titulo)

        lbl_j1 = Label(
            text="NOME DO JOGADOR 1 (X - VERDE):", color=(0, 1, 0, 1), font_size=sp(16), bold=True,
            size_hint_y=0.1
        )
        self.input_j1 = TextInput(
            text=self.jogadores["X"], multiline=False, font_size=sp(22), halign='center',
            size_hint_y=0.15
        )
        self.input_j1.bind(text=self.forcar_maiusculas)

        lbl_j2 = Label(
            text="NOME DO JOGADOR 2 (O - AMARELO):", color=(1, 1, 0, 1), font_size=sp(16), bold=True,
            size_hint_y=0.1
        )
        self.input_j2 = TextInput(
            text=self.jogadores["O"], multiline=False, font_size=sp(22), halign='center',
            size_hint_y=0.15
        )
        self.input_j2.bind(text=self.forcar_maiusculas)

        box_conteudo.add_widget(lbl_j1)
        box_conteudo.add_widget(self.input_j1)
        box_conteudo.add_widget(lbl_j2)
        box_conteudo.add_widget(self.input_j2)

        btn_iniciar = Button(
            text="CONFIRMAR E CONTINUAR",
            size_hint_y=0.25, font_size=sp(20), bold=True
        )
        btn_iniciar.bind(on_press=self.salvar_nomes)
        box_conteudo.add_widget(btn_iniciar)

        self.root_layout.add_widget(box_conteudo)

    def salvar_nomes(self, instance):
        nome1 = self.input_j1.text.strip().upper() or "JOGADOR 1"
        nome2 = self.input_j2.text.strip().upper() or "JOGADOR 2"
        self.jogadores["X"] = nome1
        self.jogadores["O"] = nome2

        self.iniciar_tabuleiro()

    def iniciar_tabuleiro(self):
        self.root_layout.clear_widgets()
        self.simbolo_atual = "X"
        self.vencedor = None
        self.botoes_vencedores = []

        self.root_layout.add_widget(self.criar_botao_voltar_topo())

        self.status_label = Label(
            text=f"JOGADOR DA VEZ: {self.jogadores[self.simbolo_atual]} ({self.simbolo_atual})",
            color=(0, 1, 0, 1),
            font_size=sp(20),
            bold=True,
            size_hint_y=0.14
        )
        self.root_layout.add_widget(self.status_label)

        anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.7)
        grid = SquareGrid(cols=3, rows=3, spacing=dp(5))

        self.botoes = []
        for i in range(3):
            linha_botoes = []
            for j in range(3):
                btn = Button(text="", font_size=sp(50), bold=True)
                btn.bind(on_press=self.fazer_jogada)
                grid.add_widget(btn)
                linha_botoes.append(btn)
            self.botoes.append(linha_botoes)

        anchor.add_widget(grid)
        self.root_layout.add_widget(anchor)

        btn_reiniciar = Button(
            text="REINICIAR JOGO", size_hint_y=0.08, font_size=sp(14)
        )
        btn_reiniciar.bind(on_press=self.reiniciar_jogo)
        self.root_layout.add_widget(btn_reiniciar)

    def fazer_jogada(self, instance):
        if instance.text != "" or self.vencedor is not None:
            return

        instance.text = self.simbolo_atual
        if self.simbolo_atual == "X":
            instance.color = (0, 1, 0, 1)
        else:
            instance.color = (1, 1, 0, 1)

        ganhou, botoes_win = self.verificar_vitoria()

        if ganhou:
            self.status_label.text = f"VENCEDOR: {self.jogadores[self.simbolo_atual]} ({self.simbolo_atual})"
            self.status_label.color = (0, 1, 0, 1) if self.simbolo_atual == "X" else (1, 1, 0, 1)
            self.vencedor = self.simbolo_atual
            self.botoes_vencedores = botoes_win
            self.evento_piscar = Clock.schedule_interval(self.piscar_mensagem, 0.5)

        elif self.verificar_empate():
            self.status_label.text = "DEU VELHA! O JOGO EMPATOU."
            self.status_label.color = (1, 0, 0, 1)
            self.vencedor = "Empate"
            self.evento_piscar = Clock.schedule_interval(self.piscar_mensagem, 0.5)

        else:
            self.simbolo_atual = "O" if self.simbolo_atual == "X" else "X"
            self.status_label.text = f"JOGADOR DA VEZ: {self.jogadores[self.simbolo_atual]} ({self.simbolo_atual})"
            self.status_label.color = (0, 1, 0, 1) if self.simbolo_atual == "X" else (1, 1, 0, 1)

    def piscar_mensagem(self, dt):
        r, g, b, a = self.status_label.color
        novo_alpha = 0 if a == 1 else 1
        self.status_label.color = (r, g, b, novo_alpha)

        for btn in self.botoes_vencedores:
            br, bg, bb, ba = btn.color
            btn.color = (br, bg, bb, novo_alpha)

    def verificar_vitoria(self):
        b = self.botoes
        for i in range(3):
            if b[i][0].text == b[i][1].text == b[i][2].text != "":
                return True, [b[i][0], b[i][1], b[i][2]]
        for i in range(3):
            if b[0][i].text == b[1][i].text == b[2][i].text != "":
                return True, [b[0][i], b[1][i], b[2][i]]
        if b[0][0].text == b[1][1].text == b[2][2].text != "":
            return True, [b[0][0], b[1][1], b[2][2]]
        if b[0][2].text == b[1][1].text == b[2][0].text != "":
            return True, [b[0][2], b[1][1], b[2][0]]
        return False, []

    def verificar_empate(self):
        for linha in self.botoes:
            for btn in linha:
                if btn.text == "":
                    return False
        return True

    def reiniciar_jogo(self, instance=None):
        if self.evento_piscar:
            self.evento_piscar.cancel()
            self.evento_piscar = None

        self.jogadores = {
            "X": "JOGADOR 1",
            "O": "JOGADOR 2"
        }
        self.mostrar_tela_nomes()


class JogoDaForcaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_tentativas = 5
        self.alfabeto = [
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
            "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
            "U", "V", "W", "X", "Y", "Z"
        ]

        self.layout_principal = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        self.layout_config = BoxLayout(orientation='vertical', spacing=dp(10))

        btn_voltar = Button(text="< VOLTAR AO MENU PRINCIPAL", size_hint_y=0.08, font_size=sp(14))
        btn_voltar.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        self.layout_config.add_widget(btn_voltar)

        self.label_instrucao = Label(text="DIGITE A PALAVRA SECRETA:", font_size=sp(20), size_hint_y=0.15)
        self.layout_config.add_widget(self.label_instrucao)

        self.input_palavra = TextInput(multiline=False, font_size=sp(26), halign='center', size_hint_y=0.15)
        self.input_palavra.bind(text=self.forcar_maiusculas)
        self.layout_config.add_widget(self.input_palavra)

        self.label_tentativas = Label(text=f"NÚMERO DE TENTATIVAS: {self.max_tentativas}", font_size=sp(18), size_hint_y=0.1)
        self.layout_config.add_widget(self.label_tentativas)

        layout_botoes_tentativas = GridLayout(cols=10, spacing=dp(3), size_hint_y=0.15)
        self.botoes_tentativas_dict = {}

        for num in range(1, 11):
            btn_num = ButtonVivo(
                text=str(num), font_size=sp(16),
                background_color=(0.2, 0.6, 1, 1) if num == self.max_tentativas else (0.3, 0.3, 0.3, 1)
            )
            btn_num.bind(on_press=self.selecionar_tentativas)
            self.botoes_tentativas_dict[num] = btn_num
            layout_botoes_tentativas.add_widget(btn_num)

        self.layout_config.add_widget(layout_botoes_tentativas)

        btn_iniciar = Button(text="COMEÇAR JOGO", font_size=sp(20), size_hint_y=0.25)
        btn_iniciar.bind(on_press=self.confirmar_palavra)
        self.layout_config.add_widget(btn_iniciar)

        self.layout_jogo = BoxLayout(orientation='vertical', spacing=dp(10))

        btn_voltar_jogo = Button(text="< VOLTAR AO MENU PRINCIPAL", size_hint_y=0.08, font_size=sp(14))
        btn_voltar_jogo.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        self.layout_jogo.add_widget(btn_voltar_jogo)

        self.status_label = Label(text="", color=(1, 1, 1, 1), font_size=sp(18), size_hint_y=0.1)
        self.layout_jogo.add_widget(self.status_label)

        self.palavra_label = Label(text="", color=(1, 1, 0, 1), font_size=sp(36), size_hint_y=0.18)
        self.layout_jogo.add_widget(self.palavra_label)

        layout_teclado = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=0.56)
        self.botoes_teclas = {}
        distribuicao = [7, 7, 7, 5]
        idx_letra = 0

        for qtd in distribuicao:
            linha_layout = BoxLayout(orientation='horizontal', spacing=dp(4))
            for _ in range(qtd):
                if idx_letra < len(self.alfabeto):
                    letra = self.alfabeto[idx_letra]
                    btn = ButtonVivo(text=letra, font_size=sp(18), bold=True, background_color=(0.2, 0.6, 1, 1))
                    btn.bind(on_press=self.fazer_tentativa)
                    linha_layout.add_widget(btn)
                    self.botoes_teclas[letra] = btn
                    idx_letra += 1
            layout_teclado.add_widget(linha_layout)

        self.layout_jogo.add_widget(layout_teclado)

        btn_reiniciar = Button(text="REINICIAR JOGO", size_hint_y=0.08, font_size=sp(14))
        btn_reiniciar.bind(on_press=self.reiniciar_jogo)
        self.layout_jogo.add_widget(btn_reiniciar)

        self.layout_principal.add_widget(self.layout_config)
        self.add_widget(self.layout_principal)

    def on_enter(self):
        self.reiniciar_jogo()

    def selecionar_tentativas(self, instance):
        self.max_tentativas = int(instance.text)
        self.label_tentativas.text = f"NÚMERO DE TENTATIVAS: {self.max_tentativas}"
        for num, btn in self.botoes_tentativas_dict.items():
            btn.background_color = (0.2, 0.6, 1, 1) if num == self.max_tentativas else (0.3, 0.3, 0.3, 1)

    def forcar_maiusculas(self, instance, value):
        instance.text = value.upper()

    def remover_acentos(self, texto):
        texto_nfkd = unicodedata.normalize('NFD', texto)
        return "".join([c for c in texto_nfkd if not unicodedata.combining(c)])

    def confirmar_palavra(self, instance):
        entrada = self.input_palavra.text.strip()
        palavra_limpa = self.remover_acentos(entrada).upper()
        palavra_filtrada = "".join([c for c in palavra_limpa if c in self.alfabeto])

        if not palavra_filtrada:
            self.label_instrucao.text = "ERRO! TENTE DE NOVO:"
            return

        self.palavra_secreta = palavra_filtrada
        self.letras_descobertas = set()
        self.tentativas_restantes = self.max_tentativas
        self.fim_de_jogo = False

        for btn in self.botoes_teclas.values():
            btn.disabled = False
            btn.color = (1, 1, 1, 1)
            btn.background_color = (0.2, 0.6, 1, 1)

        self.layout_principal.clear_widgets()
        self.layout_principal.add_widget(self.layout_jogo)
        self.atualizar_interface()

    def atualizar_interface(self):
        exibicao = " ".join([letra if letra in self.letras_descobertas else "_" for letra in self.palavra_secreta])
        self.palavra_label.text = exibicao

        qtd_caracteres = len(exibicao)
        if qtd_caracteres > 0:
            tamanho_dinamico = sp(350 / max(qtd_caracteres, 10))
            self.palavra_label.font_size = min(sp(36), max(sp(16), tamanho_dinamico))

        if not self.fim_de_jogo:
            self.status_label.color = (1, 1, 1, 1)
            self.status_label.text = f"TENTATIVAS RESTANTES: {self.tentativas_restantes}"

    def fazer_tentativa(self, instance):
        if self.fim_de_jogo:
            return

        letra = instance.text
        instance.disabled = True

        if letra in self.palavra_secreta:
            instance.background_color = (0, 1, 0, 1)
            instance.color = (1, 1, 1, 1)
            self.letras_descobertas.add(letra)
            if set(self.palavra_secreta).issubset(self.letras_descobertas):
                self.fim_de_jogo = True
                self.atualizar_interface()
                self.status_label.text = "PARABÉNS! VOCÊ VENCEU!"
                self.status_label.color = (0, 1, 0, 1)
            else:
                self.atualizar_interface()
        else:
            instance.background_color = (1, 0, 0, 1)
            instance.color = (1, 1, 1, 1)
            self.tentativas_restantes -= 1
            if self.tentativas_restantes <= 0:
                self.fim_de_jogo = True
                self.atualizar_interface()
                self.status_label.text = f"VOCÊ PERDEU! A PALAVRA ERA: {self.palavra_secreta}"
                self.status_label.color = (1, 0, 0, 1)
            else:
                self.atualizar_interface()

    def reiniciar_jogo(self, instance=None):
        self.input_palavra.text = ""
        self.label_instrucao.text = "DIGITE A PALAVRA SECRETA:"
        self.layout_principal.clear_widgets()
        self.layout_principal.add_widget(self.layout_config)


class SuiteDeJogosApp(App):
    def build(self):
        self.title = 'rodcamilo'
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(BatalhaNavalScreen(name='batalha_naval'))
        sm.add_widget(JogoDaForcaScreen(name='jogo_da_forca'))
        sm.add_widget(JogoDaVelhaScreen(name='jogo_da_velha'))
        return sm


if __name__ == '__main__':
    SuiteDeJogosApp().run()