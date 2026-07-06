import re

with open('locales/pl/LC_MESSAGES/messages.po', 'r', encoding='utf-8') as f:
    content = f.read()

translations = {
    r"\[cyan\]Syncing offers\.\.\.": "[cyan]Synchronizacja ofert...",
    r"\[cyan\]Syncing offers\.\.\. \(Found \{count\} offers so far\)": "[cyan]Synchronizacja ofert... (Znaleziono do tej pory {count} ofert)",
    r"\[bold yellow\]No new offers found\.\[/bold yellow\]": "[bold yellow]Nie znaleziono nowych ofert.[/bold yellow]",
    r"Salary": "Wynagrodzenie",
    r"Price": "Cena",
    r"Unknown": "Nieznane",
    r"Free": "Za darmo",
    r"Negotiable": "Do negocjacji",
    r"Location": "Lokalizacja",
    r"N/A": "Brak danych",
    r"URL": "URL",
    r"Save": "Zapisz",
    r"Reject": "Odrzuć",
    r"Skip": "Pomiń",
    r"Quit": "Zakończ",
    r"Session Summary - Saved: \{saved\}, Rejected: \{rejected\}, Skipped: \{skipped\}": "Podsumowanie sesji - Zapisane: {saved}, Odrzucone: {rejected}, Pominięte: {skipped}",
    r"Check for new results\? \(y/n\)": "Sprawdzić nowe wyniki? (y/n)",
    r"\[red\]Error: Please provide either --url or --query, not both\.\[/red\]": "[red]Błąd: Podaj --url albo --query, nie oba na raz.[/red]",
    r"Starting session for: \{search_param\}": "Rozpoczynanie sesji dla: {search_param}",
    r"Back": "Wstecz",
    r"Settings Menu": "Menu Ustawień",
    r"Select language": "Wybierz język",
    r"Error saving settings": "Błąd podczas zapisywania ustawień",
    r"Auto-open browser when showing offers\?": "Czy otwierać przeglądarkę automatycznie?",
    r"Create new search": "Utwórz nowe wyszukiwanie",
    r"Manage existing searches": "Zarządzaj istniejącymi wyszukiwaniami",
    r"Settings": "Ustawienia",
    r"Exit": "Wyjście",
    r"Exiting\.\.\. Goodbye!": "Wychodzenie... Do widzenia!",
    r"Enter a search query or URL:": "Wprowadź frazę wyszukiwania lub URL:",
    r"\[cyan\]Started session for: \{name\}\[/cyan\]": "[cyan]Rozpoczęto sesję dla: {name}[/cyan]",
    r"\[yellow\]No existing searches found\.\[/yellow\]": "[yellow]Nie znaleziono istniejących wyszukiwań.[/yellow]",
    r"Select a search to manage": "Wybierz wyszukiwanie do zarządzania",
    r"Manage '\{name\}'": "Zarządzaj '{name}'",
    r"Run search": "Uruchom wyszukiwanie",
    r"Delete search": "Usuń wyszukiwanie",
    r"\[cyan\]Running session: \{name\}\[/cyan\]": "[cyan]Uruchamianie sesji: {name}[/cyan]",
    r"Are you sure\? This will delete the session '\{name\}' and \{count\} linked offers\.": "Czy na pewno? Zostanie usunięta sesja '{name}' oraz {count} połączonych ofert.",
    r"\[green\]Session '\{name\}' deleted\.\[/green\]": "[green]Sesja '{name}' została usunięta.[/green]",
    r"\[yellow\]'\{choice\}' is not implemented yet\.\[/yellow\]": "[yellow]'{choice}' nie jest jeszcze zaimplementowane.[/yellow]",
    r"Language: \{lang\}": "Język: {lang}",
    r"Auto-open browser: \{auto\}": "Automatyczne otwieranie przeglądarki: {auto}",
    r"Offer-Radar": "Offer-Radar",
    r"On": "włączone",
    r"Off": "wyłączone",
    r"English": "angielski",
    r"Polish": "polski",
    r"\(Use arrow keys\)": "(Użyj strzałek)",
    r"\\nCancelled by user\\n": "\nAnulowano przez użytkownika\n"
}

lines = content.split('\n')
new_lines = []
for line in lines:
    if not line.startswith('#~'):
        new_lines.append(line)
content = '\n'.join(new_lines)

for key, value in translations.items():
    pattern = r'(msgid "' + key + r'")\nmsgstr ""'
    replacement = r'\1\nmsgstr "' + value + r'"'
    content = re.sub(pattern, replacement, content)

for key, value in translations.items():
    if key == r"Are you sure\? This will delete the session '\{name\}' and \{count\} linked offers\.":
        pattern = r'(msgid ""\n"Are you sure\? This will delete the session \'\{name\}\' and \{count\} linked "\n"offers\.")\nmsgstr ""'
        replacement = r'\1\nmsgstr "Czy na pewno? Zostanie usunięta sesja \'{name}\' oraz {count} połączonych ofert."'
        content = re.sub(pattern, replacement, content)
    elif key == r"\\nCancelled by user\\n":
        pattern = r'(msgid ""\n"\\n"\n"Cancelled by user\\n")\nmsgstr ""'
        replacement = r'\1\nmsgstr "\\nAnulowano przez użytkownika\\n"'
        content = re.sub(pattern, replacement, content)

with open('locales/pl/LC_MESSAGES/messages.po', 'w', encoding='utf-8') as f:
    f.write(content)
