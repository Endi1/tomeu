import os

from jinja2 import Template


class Entry:
    def __init__(self, parsed_entry, feed_title):
        self.feed_title = feed_title
        self.title = parsed_entry.title.replace("/", "")
        self.body = parsed_entry.description
        self.link = parsed_entry.link
        self.updated = parsed_entry.updated

    def save(self):
        location = self._get_location()
        template = self._create_template()

        f = open(location, "w+")
        f.write(template)
        f.close()

    def _get_location(self):
        return os.path.join(
            self.feed_title, self.updated + "_-_" + self.title + ".html"
        )

    def _create_template(self):
        template_file = open("./templates/entry.html", "r")
        template = template_file.read()
        template_file.close()

        rendered = Template(template)

        return rendered.render(
            entry={
                "title": self.title,
                "feed_title": self.feed_title,
                "body": self.body,
                "updated": self.updated,
                "link": self.link,
            }
        )
