from pydantic import Field,BaseModel,HttpUrl
from typing import Optional

class Input(BaseModel):
    pr_url:HttpUrl | None = Field(default=None,description="Link to the PR") #link
    repo_url:HttpUrl | None= Field(default=None,description="Link to the repo") #link
    ref:HttpUrl | None = Field(default=None,description="Brach ref") #link
    context_lines:int = Field(default=3) #link