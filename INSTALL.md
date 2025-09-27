# Instalação e Configuração

Este guia detalha os procedimentos de instalação e configuração do PPK-DRONE.

## 📋 Pré-requisitos

### Sistema Operacional
- Windows 10/11 (64-bit)
- Mínimo 4GB RAM
- 500MB espaço livre em disco

### Python (se executar código fonte)
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🚀 Opções de Instalação

### Opção 1: Executável Standalone (Recomendado)

Esta é a forma mais simples de usar o PPK-DRONE.

1. **Download**
   - Acesse [Releases](https://github.com/aleferobert/PPK_DJI/releases)
   - Baixe a última versão `PPK_Drone_vX.X.X.zip`

2. **Extração**
   ```
   PPK_Drone_vX.X.X/
   ├── PPK_Drone.exe     # Executável principal
   ├── rnx2rtkp.exe      # Processador RTKLIB
   ├── crx2rnx.exe       # Conversor Hatanaka
   ├── config.conf       # Configurações
   └── README.txt        # Instruções básicas
   ```

3. **Execução**
   - Execute `PPK_Drone.exe`
   - Não requer instalação do Python

### Opção 2: Código Fonte Python

Para desenvolvedores ou usuários avançados.

1. **Clone do Repositório**
   ```bash
   git clone https://github.com/aleferobert/PPK_DJI.git
   cd PPK_DJI
   ```

2. **Ambiente Virtual (Recomendado)**
   ```bash
   python -m venv ppk_env
   ppk_env\Scripts\activate  # Windows
   ```

3. **Instalação de Dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execução**
   ```bash
   python ppk_drone.py
   ```

## 📦 Dependências Python

```txt
tkinter>=8.6
pyproj>=3.4.0
pandas>=1.5.0
numpy>=1.21.0
Pillow>=9.0.0
```

### Instalação Manual das Dependências

```bash
pip install pyproj pandas numpy pillow
```

**Nota**: `tkinter` geralmente vem incluído com Python.

## ⚙️ Configuração Inicial

### 1. Verificação da Instalação

Execute o programa e verifique se a interface abre corretamente:

- ✅ Interface gráfica carrega
- ✅ Botões de seleção funcionam
- ✅ Campos de entrada são editáveis

### 2. Teste com Dados de Exemplo

Se você tem dados de teste, faça um processamento simples:

1. Selecione arquivos pequenos primeiro
2. Verifique se o processamento completa
3. Examine os arquivos de saída gerados

### 3. Configuração do RTKLIB

O arquivo `config.conf` contém as configurações do processamento PPK:

```ini
# Configurações principais
pos1-posmode       = kinematic  # Modo cinemático
pos1-frequency     = l1+l2+l5   # Frequências GNSS
pos1-elmask        = 10         # Máscara elevação (graus)
pos2-armode        = continuous # Resolução ambiguidade
```

#### Parâmetros Importantes

| Parâmetro | Valores | Descrição |
|-----------|---------|-----------|
| `pos1-posmode` | kinematic, static | Modo de posicionamento |
| `pos1-frequency` | l1, l1+l2, l1+l2+l5 | Frequências utilizadas |
| `pos1-elmask` | 10-15 | Ângulo mínimo de elevação |
| `pos2-armode` | continuous, fix-and-hold | Modo de resolução |

## 🔧 Configurações Avançadas

### Personalização de Projeções

Para WebODM, você pode modificar a projeção padrão editando `ppk_process.py`:

```python
# Linha ~89 em ppk_process.py
proj4_str = "+proj=utm +zone=23 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
```

Exemplos de projeções:

```python
# UTM Zona 22S (Brasil Central)
"+proj=utm +zone=22 +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

# UTM Zona 23S (Brasil Sudeste)  
"+proj=utm +zone=23 +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

# SIRGAS 2000 UTM 23S
"+proj=utm +zone=23 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
```

### Configuração de Caminhos

Se necessário, ajuste os caminhos dos executáveis em `ppk_drone.py`:

```python
# Linhas ~133-136
script_dir = os.path.dirname(os.path.abspath(__file__))
rnx2rtkp_path = os.path.join(script_dir, "rnx2rtkp.exe")
crx2rnx_path = os.path.join(script_dir, "crx2rnx.exe")
config_path = os.path.join(script_dir, "config.conf")
```

## 🔍 Verificação da Instalação

### Teste Rápido

1. **Abrir Aplicação**
   - Execute o programa
   - Verifique se todos os botões estão funcionais

2. **Teste de Conversão Coordenadas**
   ```python
   # No terminal Python, teste:
   from ppk_drone import dms_to_decimal
   resultado = dms_to_decimal("-23 34 45.6")
   print(resultado)  # Deve retornar: -23.579333...
   ```

3. **Teste de Executáveis**
   ```bash
   # Teste o RTKLIB
   rnx2rtkp.exe --help
   
   # Teste o conversor Hatanaka
   crx2rnx.exe --help
   ```

### Resolução de Problemas Comuns

#### "Módulo não encontrado"
```bash
# Instale a dependência faltante
pip install nome_do_modulo
```

#### "Executável não encontrado"
- Verifique se `rnx2rtkp.exe` e `crx2rnx.exe` estão na mesma pasta
- No código fonte, use caminhos absolutos se necessário

#### "Erro de permissão"
- Execute como administrador (se necessário)
- Verifique permissões da pasta de instalação

#### "Erro de encoding"
- Alguns arquivos RINEX podem ter encoding diferente
- O programa tentará UTF-8 e Latin-1 automaticamente

## 📂 Estrutura de Diretórios Recomendada

```
Projetos_PPK/
├── PPK_Drone/           # Instalação do programa
│   ├── PPK_Drone.exe
│   ├── rnx2rtkp.exe
│   ├── crx2rnx.exe
│   └── config.conf
└── Dados_Missoes/       # Seus dados de campo
    ├── 2024_01_15_Site1/
    │   ├── DJI_0001.JPG...
    │   ├── Evento.MRK
    │   ├── rover.24o
    │   ├── base.24o
    │   └── brdc.24n
    └── 2024_01_16_Site2/
        └── ...
```

## 🆘 Suporte

Se encontrar problemas durante a instalação:

1. **Verifique os logs** de erro no terminal
2. **Consulte as Issues** no GitHub
3. **Crie uma nova Issue** com detalhes do erro
4. **Entre em contato** através do repositório

## 📚 Próximos Passos

Após a instalação bem-sucedida:

1. Leia o [Guia de Uso](USAGE.md)
2. Teste com seus dados reais
3. Explore as configurações avançadas
4. Contribua com feedback e melhorias