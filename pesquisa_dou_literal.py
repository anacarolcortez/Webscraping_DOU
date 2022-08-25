# Documentação Selenium para Python: https://selenium-python.readthedocs.io/
# Versão passo a passo, literal
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Configura opção de tela maximizada
options = Options()
options.add_argument("--start-maximized")
options.add_argument('--headless') #opção de rodar o Selenium em segundo plano

# Abre o navegador
driver = webdriver.Chrome('driver/chromedriver', options=options)
wait = WebDriverWait(driver, 20)

def abrir_navegador(url):
    driver.get(url)

def abrir_nova_aba(link):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    abrir_navegador(link)

def fechar_aba():
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def pesquisar_palavra_chave(palavra, periodo, tipo_ato):
    input_pesquisa = wait.until(EC.visibility_of_element_located((By.ID, 'search-bar')))
    input_pesquisa.send_keys(palavra)

    link_pesquisa_avancada = wait.until(EC.element_to_be_clickable((By.ID, 'toggle-search-advanced')))
    link_pesquisa_avancada.click()

    input_periodo = wait.until(EC.element_to_be_clickable((By.XPATH, f"//label[contains(text(), '{periodo}')]/../input")))
    input_periodo.click()

    button_pesquisar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'PESQUISAR')]")))
    button_pesquisar.click()

    if "0 resultados para" not in driver.page_source:
        combo_tipo_ato = wait.until(EC.element_to_be_clickable((By.ID, 'artTypeAction')))
        combo_tipo_ato.click()

        option_ato = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{tipo_ato}')]")))
        option_ato.click()
    else:
        raise Exception("A consulta não retornou resultados")

def coletar_texto_contrato(link):
    texto_contrato = []
    abrir_nova_aba(link)

    lista_p = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "dou-paragraph")))
    for p in lista_p:
        texto_contrato.append(p.get_attribute("innerHTML"))

    fechar_aba()

    return "".join(texto_contrato)

def coletar_informacoes_contrato(resultado):
    contrato = {}

    secao_dou = resultado.find_element(By.TAG_NAME, "ol")
    itens_secao = secao_dou.find_elements(By.TAG_NAME, "li")
    contrato.update({"publicacao": itens_secao[-1].get_attribute("innerHTML")})
    contrato.update({"cidade": itens_secao[-2].get_attribute("innerHTML")})
    contrato.update({"UF": itens_secao[-3].get_attribute("innerHTML")})
    data = resultado.find_element(By.CLASS_NAME, "date-marker")
    contrato.update({"data": data.get_attribute("innerHTML")})

    link_contrato = resultado.find_element(By.TAG_NAME, "a").get_attribute("href")
    texto_contrato = coletar_texto_contrato(link_contrato)
    contrato.update({"texto_contrato": texto_contrato})

    return contrato

def coletar_informacoes_pagina_inteira():
    lista_contratos = []
    lista_resultados = wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//div[@class='resultado']")))
    for resultado in lista_resultados:
        lista_contratos.append(coletar_informacoes_contrato(resultado))
    return lista_contratos

def numero_paginas():
    xpath_btn = "//li[contains(@class, 'page-item')]/button"
    lista_btn = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_btn)))
    btn_ultima_pg = lista_btn[-2].get_attribute("innerHTML")
    return int(btn_ultima_pg)

def coletar_informacoes_todas_paginas():
    resultados_totais = []
    pgs = numero_paginas()

    resultados_totais = coletar_informacoes_pagina_inteira()

    if pgs > 1:
        for pagina in range(2, pgs+1):
            xpath_btn_pg = f"//li[@id='{pagina}']/button"
            wait.until(EC.presence_of_element_located((By.XPATH, xpath_btn_pg))).click()
            resultado_pagina = coletar_informacoes_pagina_inteira()
            for resultado in resultado_pagina:
                resultados_totais.append(resultado)

    return resultados_totais

def create_dataframe(dataframe):
    df = pd.DataFrame(dataframe)
    df.to_csv(r'dados/dou_contratos_shows_mensal.csv',
              index=False, sep=";")

def passo_a_passo():
    try:
        abrir_navegador("https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados")
        pesquisar_palavra_chave("show", "Último mês", "Extrato de Contrato")
        dados = coletar_informacoes_todas_paginas()
        create_dataframe(dados)
    except Exception as error:
        print(error)
    driver.close()

passo_a_passo()
