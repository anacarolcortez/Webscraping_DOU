# Documentação Selenium para Python: https://selenium-python.readthedocs.io/

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

driver = webdriver.Chrome('driver/chromedriver')
wait = WebDriverWait(driver, 30)


def open_browser(site, title):
    driver.get(site)
    assert title in driver.title


def close_window():
    driver.close()


def search(xpath, word):
    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.send_keys(word)
    element.send_keys(Keys.ENTER)


def advanced_search(label):
    link_pesquisa_avancada = "//a[@id='toggle-search-advanced']"
    option_label = f"//label[contains(text(),'{label}')]//../input"
    button_pesquisar = "//button[contains(text(), 'PESQUISAR')]"
    click_element(link_pesquisa_avancada)
    click_element(option_label)
    click_element(button_pesquisar)


def click_element(xpath):
    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()


def get_total_pages():
    last_page_btn = "//li[contains(@class, 'page-item')]/button"
    elements = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, last_page_btn)))
    return elements[-2].get_attribute("innerHTML")


def new_window(link):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(link)


def back_to_main_window():
    close_window()
    driver.switch_to.window(driver.window_handles[0])
    driver.implicitly_wait(3)


def get_show_fee(text):
    expences = re.search(r'', text)
    return expences


def get_contract_info(link):
    texto_completo = []
    new_window(link)

    textos = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'dou-paragraph')))

    for texto in textos:
        texto_completo.append(texto.get_attribute("innerHTML"))

    #valor = get_show_fee(texto_completo)
    back_to_main_window()

    return "".join(texto_completo)


def get_contracts_info_from_page():
    contracts_list = []

    # Lista todos os resultados encontrados na página vigente
    div_resultados = "//div[@class='resultado']"
    resultados_list = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, div_resultados)))

    # Itera sobre cada resultado, para armazenar informações de cada contrato da página
    for resultado in resultados_list:
        contract = {}

        # Armazena informações dos órgãos contratantes
        parent_contratantes = resultado.find_element(
            By.TAG_NAME, "ol")
        entidades_list = parent_contratantes.find_elements(
            By.TAG_NAME, 'li')
        contract.update(
            {"UF": entidades_list[-3].get_attribute("innerHTML")})
        contract.update(
            {"cidade": entidades_list[-2].get_attribute("innerHTML")})
        contract.update(
            {"publicacao": entidades_list[-1].get_attribute("innerHTML")})

        # Armazena data da publicação
        data = resultado.find_element(
            By.CLASS_NAME, 'date-marker').get_attribute("innerHTML")
        contract.update({"data_publicacao": data})

        # Armazena título e link da publicação
        contrato = resultado.find_element(By.TAG_NAME, 'h5')
        link_contrato = contrato.find_element(By.TAG_NAME, 'a')
        href_contrato = link_contrato.get_attribute("href")
        nome_contrato = link_contrato.get_attribute("innerHTML")
        contract.update({"link": href_contrato})
        contract.update({"titulo_publicacao": nome_contrato})

        texto_contrato = get_contract_info(href_contrato)
        contract.update({"texto_contrato": texto_contrato})

        contracts_list.append(contract)

    # print(contracts_list)

    return contracts_list


def get_all_contracts():
    contracts = []

    total_pages = int(get_total_pages())

    # Pega todas as informações dos contratos da primeira página
    lista_pg_1 = get_contracts_info_from_page()
    for item in lista_pg_1:
        contracts.append(item)

    if total_pages > 1:
        for i in range(2, total_pages+1):
            btn_number_page = f"//li[@id='{i}']/button"
            wait.until(
                EC.visibility_of_element_located((By.XPATH, btn_number_page))).click()
            lista_pg = get_contracts_info_from_page()
            for item in lista_pg:
                contracts.append(item)

    # print(contracts)
    return contracts


def create_dataframe(dataframe):
    df = pd.DataFrame(dataframe)
    df.to_csv(r'dados/dou_contratos_shows_doze_meses.csv',
              index=False, sep=";")


def main():
    # Elementos da página de pesquisa
    div_imput = "//input[@id='search-bar']"
    div_tipo_ato = "//div[@id='artType']"
    link_extrato_contrato = "//a[contains(text(),'Extrato de Contrato')]"

    # Abrir site do Diário Oficial da União na página de pesquisa
    url_principal = "https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados"
    open_browser(url_principal, "Imprensa Nacional")

    # Pesquisar pela palavra-chave "show"
    search(div_imput, "show")

    # Filtrar consulta por período: últimos doze meses
    advanced_search("Último ano")

    # Filtrar pesquisa por Tipo de Ato: "Extrato de Contrato"
    click_element(div_tipo_ato)
    click_element(link_extrato_contrato)

    # Armazenar informações de todos os contratos obtidos na pesquisa
    dados = get_all_contracts()

    # Cria dataframe com dados para análise posterior
    create_dataframe(dados)

    # Fechar o navegador
    close_window()


if __name__ == "__main__":
    main()
