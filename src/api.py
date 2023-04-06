"""A story tagger designed to return metadata for a given input summary. By Sil."""
from enum import Enum
from typing import Optional, List, Dict, Any
from steamship import Steamship, File, Block
from steamship.invocable import post, PackageService, InvocationContext

from pydantic import BaseModel
from retry import retry


class Output(BaseModel):
    setting: Optional[str]
    character: Optional[str]
    genre: Optional[str]
    logline: Optional[str]
    tag: Optional[str]
    ifyoulike: Optional[str]


class SteamshipPackage(PackageService):
    def __init__(
        self,
        client: Steamship = "sil",
        config: Dict[str, any] = None,
        context: InvocationContext = None,
    ):
        super().__init__(client, config, context)


    @retry(SyntaxError, tries=3)
    def classify(self, job, tagger) -> dict:
        tag_task = job.tag(tagger.handle)
        tag_task.wait()
        job.refresh()
        return eval(job.blocks[0].tags[0].value.get(TagValueKey.STRING_VALUE.value))


    @post("generate")
    def generate(self, summary: str = "Story Summary") -> dict:

        job = File.create(self.client, blocks = [Block(text = summary)])

        tagger = self.client.use_plugin(
            plugin_handle = "prompt-generation-trainable-default",
            version = '0.0.22',
            config = {"max_words" : 600,
                      "openai_api_key" : "",
                      "tag_kind": "training_generation",
                      "temperature": 0.5,
                      "num_completions": 1},
            instance_handle = "curie-label")

        tags = self.classify(job, tagger)

        job.delete()

        output = Output(
            setting = tags["setting"],
            character = tags["character"],
            genre = tags["genre"],
            logline = tags["logline"],
            tag = tags["tag"],
            ifyoulike = tags["ifyoulike"])

        return output
