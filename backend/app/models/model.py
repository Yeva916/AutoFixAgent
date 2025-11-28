from pydantic import Field,BaseModel,HttpUrl
from typing import Literal

class Input(BaseModel):
    pr_url:HttpUrl | None = Field(default=None,description="Link to the PR") #link
    repo_url:HttpUrl | None= Field(default=None,description="Link to the repo") #link
    ref:HttpUrl | None = Field(default=None,description="Brach ref") #link
    context_lines:int = Field(default=3) #link

# class Digonostic(BaseModel):
#     tool:Literal['flake8','pylint','mypy']
#     file_path:str
#     line:int 
#     column:int
#     code:Literal['E','W']
#     severity:Literal['error','warning'] 
#     message:str
#     raw:str | None = None