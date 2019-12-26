# Image Specification for Buildout+Test for GitHub Actions
# ========================================================
#
# Not reusable for generic Plone sites; this is just for EDRN P5.

FROM plone/plone:5.1.5


# Metadata
# ========

LABEL "com.github.actions.name"="Buildout"
LABEL "com.github.actions.description"="Bootstraps and builds-out in the style of zc.buildout"
LABEL "com.github.actions.icon"="meh"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="https://github.com/EDRN/P5.git"
LABEL "homepage"="https://edrn.nci.nih.gov/"
LABEL "maintainer"="Sean Kelly <kelly@seankelly.biz>"


# Additional Installations
# ========================
#
# For P5, I need additional libraries

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libldap2-dev \
        libsasl2-dev \
        build-essential \
        zlib1g-dev \
        libjpeg-dev \
        libxml2-dev \
        libxslt1-dev \
        curl \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /root/.buildout

# Avoid re-downloading Plone; note this must get copied to $HOME which changes
# from /root to /github/home by GitHub Actions; the ``entrypoint.sh`` takes
# care of that
ADD default.cfg /root/.buildout/default.cfg

# The entry point
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
