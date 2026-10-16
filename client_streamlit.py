import streamlit as st
import requests
import json
import pandas as pd
from assuntos import assuntos_dict
from meios_publicacao import meios_dict
from tipos_normas import tipos_dict
from orgaos import orgaos_vinculados_dict

URL_VALIDADOR = "http://localhost:8000/validar"


st.set_page_config(
    page_title="Simulação LEGIS",
    layout="wide"
)

st.title("Simulação LEGIS")
st.caption("Comunicação com o serviço de validação")


# DADOS DA NORMA
st.subheader("Dados da norma")

col1, col2 = st.columns(2)

id_orgao_cadastrante = 272

with col1:

    esfera_governamental = {1: 'Municipal', 2:'Estadual'}
    id_esfera_governamental = st.selectbox(
        "Esfera Governamental *", options=esfera_governamental.keys(),
        format_func=lambda id_esfera_governamental: esfera_governamental[id_esfera_governamental]
    )

    id_tipo_norma = st.selectbox(
        "Tipo da Norma *", options=tipos_dict.keys(),
        format_func=lambda id_tipo_norma: tipos_dict[id_tipo_norma]
    )

    ano_norma = st.number_input(
        "Ano *",
        min_value=1900,
        max_value=2026,
        value=2026
    )

    data_inicio_vigencia = st.date_input(
        "Data de Início da Vigência *", format='DD/MM/YYYY'
    )

    area_atuacao = {1:'Civil', 2:'Militar', 3:'Civil/Militar'}
    id_area_atuacao = st.selectbox(
        "Área de Atuação *", options=area_atuacao.keys(),
        format_func=lambda id_area_atuacao: area_atuacao[id_area_atuacao]
    )
        
    id_meio_publicacao = st.selectbox(
        "Meio de Publicação *", options=meios_dict.keys(),
        format_func=lambda id_meio_publicacao: meios_dict[id_meio_publicacao]
    )
   
   
with col2:
    ente = {1: 'Natal'}
    id_ente = st.selectbox(
        "Ente *", options=ente.keys(), disabled=True,
        format_func=lambda id_ente: ente[id_ente]
    )
    
    numero_norma = st.text_input(
        "Número *", placeholder='Digite o Número da Norma'
    )

    
    data_publicacao = st.date_input(
        "Data de Publicação *", format='DD/MM/YYYY'
    )

    data_fim_vigencia = st.date_input(
        "Data de Fim da Vigência", format='DD/MM/YYYY'
    )

    endereco_eletronico = st.text_input(
        "Endereço Eletrônico",
        placeholder="Exemplo: https://www.google.com.br"
    )  

col3, col4 = st.columns(2)
with col3:
    ementa = st.text_area(
            "Ementa *",
           placeholder='Digite a Descrição da Ementa'
        )

with col4:
    arquivo = st.file_uploader(
        "Anexo *", 
        accept_multiple_files=False,
        type=["pdf"], max_upload_size=10, 
    )
    
# RELACIONAMENTOS
st.subheader("Relacionamentos")

col5, col6 = st.columns(2)

with col5:
    id_assuntos = st.multiselect(
        "Assunto da Norma *", options=assuntos_dict.keys(),
        format_func=lambda id_assunto:assuntos_dict[id_assunto],
        placeholder='Selecione um assunto de norma'
    )
    st.write(id_assuntos)

with col6:
    id_orgaos = st.multiselect(
        "Órgão *", options=orgaos_vinculados_dict.keys(),
        format_func=lambda id_orgao:orgaos_vinculados_dict[id_orgao],
        placeholder='Selecione um órgão'
    )

    st.write(id_orgaos)

# ENVIO PARA O VALIDADOR
if st.button(
    "Enviar para validação",
    type="primary"
):

    if arquivo is None:

        st.warning(
            "Selecione o PDF antes de enviar."
        )

        st.stop()

    # --------------------------------------------------------
    # Monta o mesmo JSON utilizado pelo LEGIS
    # --------------------------------------------------------
    dados = {

        "idTipoNorma": id_tipo_norma,
        "idAreaAtuacao":  id_area_atuacao,
        "idMeioPublicacao": id_meio_publicacao,
        "idEsferaGovernamental": id_esfera_governamental,
        "idCidade": id_ente,
        "idOrgaoCadastrante": id_orgao_cadastrante,

        "numeroNorma": numero_norma,
        "anoNorma": ano_norma,

        "ementa": ementa,

        "dataPublicacao": str(data_publicacao),
        "dataInicioVigencia": str(data_inicio_vigencia),
        "dataFimVigencia": '' if str(data_inicio_vigencia) == str(data_fim_vigencia) else str(data_fim_vigencia),

        "enderecoEletronico": endereco_eletronico,

        "legislacaoAssuntoNorma": [
            {
                "idAssuntoNorma": id_assunto
            } for id_assunto in id_assuntos
        ],

        "legislacaoOrgao": [
            {
                "idOrgao": id_orgao
            } for id_orgao in id_orgaos
        ]
    }


    # --------------------------------------------------------
    # Prepara o arquivo
    # --------------------------------------------------------

    files = {

        "file": (
            arquivo.name,
            arquivo.getvalue(),
            "application/pdf"
        )
    }


    data = {

        "dados": json.dumps(
            dados,
            ensure_ascii=False
        )
    }

    # --------------------------------------------------------
    # Comunicação com o FastAPI
    # --------------------------------------------------------
    with st.spinner(
        "Enviando dados para o serviço validador..."
    ):

        try:

            response = requests.post(
                URL_VALIDADOR,
                data=data,
                files=files,
                timeout=60
            )


        except requests.exceptions.ConnectionError:

            st.error(
                "Não foi possível conectar ao serviço validador."
            )

            st.info(
                "Verifique se o FastAPI está executando em "
                "http://localhost:8000"
            )

            st.stop()


        except requests.exceptions.Timeout:

            st.error(
                "O serviço validador demorou muito para responder."
            )

            st.stop()


    # RESULTADO
    if response.ok:

        resultado = response.json()

        st.success(
            "Dados validados com sucesso!"
        )

        # DataFrame dos dados enviados
        df_dados = pd.json_normalize(dados)

        # DataFrame dos resultados da IA
        df_resultados = pd.json_normalize(resultado["classificacao_ia"])


        # Valores enviados pelo formulário
        tipo_enviado = df_dados.loc[0, "idTipoNorma"]
        numero_enviado = df_dados.loc[0, "numeroNorma"]
        ano_enviado = df_dados.loc[0, "anoNorma"]

        # Valores obtidos pela IA
        tipo_ia = df_resultados.loc[0, "tipo"]
        numero_ia = df_resultados.loc[0, "numero"]
        ano_ia = df_resultados.loc[0, "ano"]


        # Monta o DataFrame comparativo
        df_comparativo = pd.DataFrame([
            {
                "Campo": "Tipo da norma",
                "Valor enviado": tipo_enviado,
                "Valor obtido pela validação": tipo_ia
            },
            {
                "Campo": "Número da norma",
                "Valor enviado": str(numero_enviado),
                "Valor obtido pela validação": str(numero_ia)
            },
            {
                "Campo": "Ano da norma",
                "Valor enviado": str(ano_enviado),
                "Valor obtido pela validação": str(ano_ia)
            }
        ])

        # Normaliza os valores para comparar
        df_comparativo["Conferência"] = df_comparativo.apply(
            lambda linha: (
                "✅​"
                if str(linha["Valor enviado"]).strip().upper()
                == str(linha["Valor obtido pela validação"]).strip().upper()
                else "❌​"
            ),
            axis=1
        )

        st.subheader("Comparativo dos dados enviados e da IA")
        st.dataframe(df_comparativo, use_container_width=True, hide_index=True)


        # # Informações do arquivo
        # if "arquivo" in resultado:

        #     st.subheader("Informações do PDF")

        #     info = resultado["arquivo"]

        #     col1, col2, col3 = st.columns(3)


    else:

        st.error(
            f"Erro retornado pelo serviço: "
            f"{response.status_code}"
        )

        st.code(
            response.text
        )