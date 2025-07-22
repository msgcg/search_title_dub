import requests
import re
from urllib.parse import urljoin, urlparse
import time

def find_duplicate_titles_improved(start_url):
    """
    Улучшенная версия: сканирует сайт, находя дубликаты заголовков,
    с улучшенной нормализацией URL и пропуском ссылок на файлы.
    """
    titles = {}
    # Для очереди используем оригинальные URL, чтобы переходить по ссылкам как есть
    urls_to_visit = [start_url]
    # Для посещенных используем нормализованные URL, чтобы не ходить по кругу
    visited_normalized_urls = set()
    start_time = time.time()
    max_urls = 200

    # Расширения файлов, которые нужно игнорировать
    excluded_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.docx', '.xlsx', '.zip', '.rar', '.mp3', '.mp4']

    print("--- Начало сканирования (улучшенная версия) ---")
    print(f"Стартовый URL: {start_url}")

    def normalize_url(url):
        # Приводим URL к единому виду: без протокола, www и слэша в конце
        p_url = urlparse(url)
        # Убираем 'www.' из домена
        netloc = p_url.netloc.replace('www.', '')
        # Собираем и убираем слэш
        return (netloc + p_url.path).rstrip('/')

    # Сразу добавляем стартовый URL в посещенные
    visited_normalized_urls.add(normalize_url(start_url))

    title_regex = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
    link_regex = re.compile(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"', re.IGNORECASE)

    processed_count = 0
    while urls_to_visit and processed_count < max_urls:
        url = urls_to_visit.pop(0)
        processed_count += 1

        print(f"\nОбрабатывается ({processed_count}/{max_urls}): {url}")
        print(f"URL в очереди: {len(urls_to_visit)}")

        try:
            # Используем stream=True и headers, чтобы сначала проверить тип контента
            head_response = requests.head(url, timeout=5, allow_redirects=True)
            content_type = head_response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                print(f"  -> Пропуск (не HTML): {content_type}")
                continue

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except requests.exceptions.RequestException as e:
            print(f"  -> Ошибка при загрузке: {e}")
            continue

        title_match = title_regex.search(html_content)
        if title_match:
            title = title_match.group(1).strip()
            print(f"  -> Найден Title: '{title}'")
            if title in titles:
                titles[title].append(url)
            else:
                titles[title] = [url]
        else:
            print("  -> Title не найден.")

        links = link_regex.findall(html_content)
        new_links_found = 0
        for link in links:
            # Пропускаем "mailto", "tel" и якорные ссылки
            if link.startswith(('mailto:', 'tel:', '#')):
                continue

            absolute_link = urljoin(url, link)
            
            # Проверяем на расширения файлов
            if any(absolute_link.lower().endswith(ext) for ext in excluded_extensions):
                continue

            # Нормализуем для проверки на дубли в очереди
            normalized_link = normalize_url(absolute_link)

            # Проверяем, что ссылка с того же домена и еще не обрабатывалась
            if urlparse(absolute_link).netloc == urlparse(start_url).netloc:
                if normalized_link not in visited_normalized_urls:
                    urls_to_visit.append(absolute_link)
                    visited_normalized_urls.add(normalized_link)
                    new_links_found += 1
        print(f"  -> Найдено {len(links)} ссылок, добавлено {new_links_found} новых URL в очередь.")

    end_time = time.time()
    print("\n--- Сканирование завершено ---")
    print(f"Затрачено времени: {end_time - start_time:.2f} секунд")
    print(f"Всего обработано URL: {processed_count}")
    print(f"Всего найдено уникальных Title: {len(titles)}")

    duplicate_titles = {title: urls for title, urls in titles.items() if len(urls) > 1}
    return duplicate_titles

if __name__ == '__main__':
    # Запускаем улучшенную проверку
    duplicate_titles = find_duplicate_titles_improved('http://uzi-samara.ru/')

    if duplicate_titles:
        print("\n--- Найдены дубликаты мета-тегов Title: ---")
        for title, urls in duplicate_titles.items():
            print(f"\nTitle: '{title}'")
            for url in urls:
                print(f"  - {url}")
    else:
        print("\n--- Дубликаты мета-тегов Title не найдены. ---")