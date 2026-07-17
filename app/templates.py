"""模板引擎模块（独立文件，避免循环导入）"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
