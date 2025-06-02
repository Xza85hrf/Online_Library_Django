#!/usr/bin/env python
"""
Skrypt do aktualizacji ścieżek URL w szablonach Django.
Usuwa prefiks 'library:' z adresów URL.
"""
import os
import re
from pathlib import Path

def update_template_urls(directory):
    """
    Aktualizuje ścieżki URL w szablonach Django, usuwając prefiks 'library:'.
    
    Args:
        directory (str): Ścieżka do katalogu z szablonami
    """
    # Wzorzec do wyszukiwania URL-i z prefiksem 'library:'
    pattern = r"{% url 'library:([^']+)'"
    replacement = r"{% url '\1'"
    
    # Liczniki
    files_processed = 0
    files_updated = 0
    urls_updated = 0
    
    # Przejście przez wszystkie pliki HTML w katalogu i podkatalogach
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # Odczytanie zawartości pliku
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Sprawdzenie, czy plik zawiera wzorzec
                if "{% url 'library:" in content:
                    # Aktualizacja URL-i
                    updated_content, count = re.subn(pattern, replacement, content)
                    
                    # Zapisanie zaktualizowanej zawartości
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    print(f"Zaktualizowano {count} URL-i w pliku {file_path}")
                    files_updated += 1
                    urls_updated += count
                
                files_processed += 1
    
    print(f"\nPodsumowanie:")
    print(f"Przetworzono plików: {files_processed}")
    print(f"Zaktualizowano plików: {files_updated}")
    print(f"Zaktualizowano URL-i: {urls_updated}")

if __name__ == "__main__":
    # Ścieżka do katalogu z szablonami
    templates_dir = Path("templates")
    
    # Aktualizacja URL-i
    update_template_urls(templates_dir)
