import requests, bs4

class unibo_crawler:
    def run(self):
        r = requests.get('http://www.unibo.it/UniboWeb/UniboSearch/Rubrica.aspx?tab=PersonePanel&mode=advanced&query=%2binizialecognome%3aA+%2btipo%3adoc')
        soup = bs4.BeautifulSoup(r.text.replace('<br />', ' '), 'html.parser')
        contacts = []

        for table in soup.find_all('table', class_='contact vcard'):
            name = table.find('td', class_='fn name').string.strip()
            organization = table.find('tr', class_='org').td.string.strip()
            role = table.find('tr', class_='role').td.string.strip()

            contact_data = {'name': name, 'role': role, 'org': organization}
            contacts.append(contact_data)
            print(contact_data)

crawler = unibo_crawler()
crawler.run()
