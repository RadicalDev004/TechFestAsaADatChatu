import os
from starlette.responses import HTMLResponse


class HomeController:
    def index(self):
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))  # D:\Work\TechFestAsaADatChatu
        template_path = os.path.join(project_root, 'Frontend', 'home.html')
        print(template_path)
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)