# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não Lançado]

### Planejado
- Suporte a múltiplas missões de voo
- Interface para edição de configurações RTKLIB
- Visualização de trajetória em mapa
- Relatórios de qualidade automatizados

## [1.2.0] - 2024-XX-XX

### Adicionado
- Suporte a múltiplos formatos de saída (DJI Terra e WebODM)
- Conversão automática de arquivos Hatanaka (.??D → .??O)
- Validação de coordenadas extraídas dos arquivos RINEX
- Interface para entrada manual de coordenadas da base em GMS
- Ícone personalizado para o executável
- Arquivo de configuração .spec para PyInstaller

### Melhorado
- Interface gráfica mais intuitiva
- Tratamento de erros mais robusto
- Mensagens de status mais informativas
- Documentação completa do projeto

### Corrigido
- Problema na conversão de ângulos radianos para graus
- Erro na interpolação temporal para imagens sem timestamp
- Tratamento de arquivos com encoding diferente

## [1.1.0] - 2024-XX-XX

### Adicionado
- Módulo separado `ppk_process.py` para reutilização
- Suporte a projeções cartográficas customizadas
- Interpolação temporal de posições GNSS
- Extração automática de ângulos de atitude (pitch, roll, yaw)

### Melhorado
- Otimização do processamento para grandes volumes de dados
- Melhor organização do código
- Validação de entrada de dados

## [1.0.0] - 2024-XX-XX

### Adicionado
- Interface gráfica principal com Tkinter
- Integração com RTKLIB (rnx2rtkp)
- Processamento de arquivos .MRK do DJI
- Leitura de arquivos RINEX (.OBS, .NAV)
- Conversão de sistemas de coordenadas
- Geração de arquivo de saída CSV
- Configurações básicas do RTKLIB

### Características Iniciais
- Seleção de arquivos via interface gráfica
- Processamento PPK automatizado
- Extração de coordenadas dos headers RINEX
- Conversão GMS ↔ Decimal
- Associação temporal imagem-posição