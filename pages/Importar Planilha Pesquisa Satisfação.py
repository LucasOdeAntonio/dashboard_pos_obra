from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Inicializar o driver (exemplo com Chrome)
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

# 1. Acessar página de login e efetuar login
driver.get("https://posobravalorreal.com.br/admin/")
print("[INFO] Página de login aberta.")

username_input = wait.until(EC.presence_of_element_located(
    (By.XPATH, "//input[@type='text' or @name='usuario' or contains(@id, 'user')]")
))
password_input = wait.until(EC.presence_of_element_located(
    (By.XPATH, "//input[@type='password' or @name='senha' or contains(@id, 'pass')]")
))
username_input.send_keys("lucas")
password_input.send_keys("55365883")
password_input.send_keys(Keys.RETURN)
print("[INFO] Login enviado.")

# Aguarda 10 segundos para garantir que a página pós-login esteja totalmente carregada
time.sleep(10)

# 2. Clicar no dropdown "Pesquisa"
try:
    dropdown = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@class, 'nav-link dropdown-toggle') and contains(., 'Pesquisa')]")
    ))
    dropdown.click()
    print("[INFO] Dropdown 'Pesquisa' clicado.")
except Exception as e:
    print("Erro ao clicar no dropdown 'Pesquisa':", e)
    driver.quit()
    exit()

# 3. Clicar no item "Resultado da Pesquisa" do dropdown
try:
    resultado_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@class, 'dropdown-item') and contains(., 'Resultado da Pesquisa')]")
    ))
    resultado_link.click()
    print("[INFO] Tela 'Resultado da Pesquisa' aberta.")
except Exception as e:
    print("Erro ao clicar no link 'Resultado da Pesquisa':", e)
    driver.quit()
    exit()

# 4. Configurar o filtro para exibir "Todos"
try:
    select_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//select[@name='tabpesquisas_length']")
    ))
    select = Select(select_element)
    select.select_by_value("-1")  # O valor "-1" corresponde à opção "Todos"
    print("[INFO] Filtro alterado para 'Todos'.")
except Exception as e:
    print("Erro ao alterar filtro:", e)

# Aguarda atualização dos dados (ajuste o tempo conforme necessário)
time.sleep(2)

# 5. Scraping das métricas do Dashboard

# 5.1. Primeira coluna – Métrica (ex: "123")
try:
    metric1 = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@class='col-12 text-center']//span[contains(@class, 'text-success')]")
    )).text
    print("Métrica 1:", metric1)
except Exception as e:
    print("Erro ao extrair Métrica 1:", e)
    metric1 = None

# 5.2. Segunda coluna – Métrica com valor e porcentagem
try:
    metric2_value = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//span[contains(@class, 'text-primary') and contains(@class, 'fs-6') and contains(@class, 'fw-bold')]")
    )).text
    metric2_percentage = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//span[contains(@class, 'text-info') and contains(@class, 'fs-1') and contains(@class, 'fw-bold')]")
    )).text
    print("Métrica 2:", metric2_value, metric2_percentage)
except Exception as e:
    print("Erro ao extrair Métrica 2:", e)
    metric2_value = None
    metric2_percentage = None

# 5.3. Terceira coluna – Média Geral (calculada a partir das notas das perguntas)
try:
    rating_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'fs-3') and contains(@class, 'fw-bold') and contains(@class, 'me-2') and contains(@class, 'text-success')]")
    ratings = [float(elem.text) for elem in rating_elements]
    if ratings:
        media_geral = sum(ratings) / len(ratings)
        print("Média Geral calculada:", round(media_geral, 2))
    else:
        print("Nenhuma nota encontrada para calcular a Média Geral.")
        media_geral = None
except Exception as e:
    print("Erro ao calcular Média Geral:", e)
    media_geral = None

# 6. Scraping da tabela "Resultado por PERGUNTAS"

# 6.1. Extração do cabeçalho
try:
    header_perguntas = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//th[contains(., 'Perguntas')]")
    )).text
    header_media = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//th[contains(., 'Média')]")
    )).text
    print("Cabeçalho da Tabela:", header_perguntas, "-", header_media)
except Exception as e:
    print("Erro ao extrair cabeçalho da tabela:", e)
    header_perguntas = None
    header_media = None

# 6.2. Extração das linhas (perguntas e suas respectivas notas)
try:
    question_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'ms-3')]")
    note_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'fs-3') and contains(@class, 'fw-bold') and contains(@class, 'me-2') and contains(@class, 'text-success')]")
    questions = [elem.text for elem in question_elements]
    notes = [elem.text for elem in note_elements]
    
    # Ajuste para garantir que as duas listas tenham o mesmo tamanho
    min_len = min(len(questions), len(notes))
    questions = questions[:min_len]
    notes = notes[:min_len]
    
    print("\nResultado por Perguntas:")
    for q, n in zip(questions, notes):
        print("Pergunta:", q, "| Nota:", n)
except Exception as e:
    print("Erro ao extrair dados da tabela de perguntas:", e)
    questions = []
    notes = []

# Encerrar o driver
driver.quit()

# Salvar os dados em uma planilha Excel "nps.xlsx"

# Criar DataFrame para as métricas
data_metrics = {
    "Métrica": ["Métrica 1", "Métrica 2", "Média Geral"],
    "Valor": [
        metric1, 
        f"{metric2_value} {metric2_percentage}" if metric2_value and metric2_percentage else None, 
        round(media_geral, 2) if media_geral is not None else None
    ]
}
df_metrics = pd.DataFrame(data_metrics)

# Criar DataFrame para a tabela de perguntas e notas
df_questions = pd.DataFrame({"Pergunta": questions, "Nota": notes})

# Salvar em um arquivo Excel com duas abas: "Métricas" e "Perguntas"
with pd.ExcelWriter("nps.xlsx", engine="openpyxl") as writer:
    df_metrics.to_excel(writer, sheet_name="Métricas", index=False)
    df_questions.to_excel(writer, sheet_name="Perguntas", index=False)

print("[INFO] Planilha nps.xlsx salva com sucesso!")
