# Image Specification for Buildout for GitHub Actions
# ===================================================

FROM python:2.7

LABEL "com.github.actions.name"="Buildout"
LABEL "com.github.actions.description"="Bootstraps and builds-out in the style of zc.buildout"
LABEL "com.github.actions.icon"="meh"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="https://github.com/EDRN/P5.git"
LABEL "homepage"="https://edrn.nci.nih.gov/"
LABEL "maintainer"="Sean Kelly <kelly@seankelly.biz>"

ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
