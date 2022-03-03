#!/usr/bin/env bash

set -e

SCRIPT_DIR=$(dirname $0)
BASE_DIR=$(realpath ${SCRIPT_DIR}/..)

DEBIAN_PACKAGE_BASE_NAME={{ var.setup.debian_package_name }}_{{ var.setup.version }}_{{ var.setup.debian_package_revision }}
DEBIAN_PACKAGE_NAME=${BASE_DIR}/{{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}.deb

if [ "${REPO_DOWNLOAD_BASE_URL}" == "" ] ; then
  echo "WARNING: No download URL REPO_DOWNLOAD_BASE_URL found in environment. Some Docker images may not be built correctly!"
else
  echo "Using URL ${REPO_DOWNLOAD_BASE_URL} for downloading zips from git repository..."
fi

{% for (context, upload) in var.setup.docker_contexts %}
echo "Build docker image in context directory '{{ context }}'..."
CONTEXT_DIR=${BASE_DIR}/{{ var.setup.docker_context_dir }}/{{ context }}
ASSETS_DIR=${CONTEXT_DIR}/assets
REVISION={{ var.setup.GIT_BRANCH }}-{{ var.setup.debian_package_revision }}

if [ -d ${CONTEXT_DIR} ]; then
    if [ -f ${DEBIAN_PACKAGE_NAME} ] ; then
        echo "Copy Debian package ${DEBIAN_PACKAGE_NAME} into the container assets..."
        cp -a ${DEBIAN_PACKAGE_NAME} ${ASSETS_DIR}/{{ var.setup.debian_package_name }}.deb
    else
        echo "ERROR: cannot find Debian package ${DEBIAN_PACKAGE_NAME}!"
        exit 1
    fi
fi

docker build -t {{ var.setup.docker_registry_org_unit }}/{{ context }}:${REVISION} \
    --build-arg TAG=${REVISION} \
    --build-arg BRANCH=${GIT_BRANCH} \
    --build-arg REPO_DOWNLOAD_BASE_URL=${REPO_DOWNLOAD_BASE_URL} \
    --build-arg TEST_PYPI_EXTRA_INDEX=${TEST_PYPI_EXTRA_INDEX} \
    --build-arg DOCKER_REGISTRY={{ var.setup.docker_registry}} \
    --build-arg DOCKER_REGISTRY_ORG_UNIT={{ var.setup.docker_registry_org_unit }} \
    ${CONTEXT_DIR}
{% if var.setup.GIT_BRANCH == var.setup.publish_latest_docker_image %}
docker tag {{ var.setup.docker_registry_org_unit }}/{{ context }}:${REVISION} \
    {{ var.setup.docker_registry_org_unit }}/{{ context }}:latest
{% endif -%}
{% if upload -%}
docker tag {{ var.setup.docker_registry_org_unit }}/{{ context }}:${REVISION} \
    {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_org_unit }}/{{ context }}:${REVISION}
{% if var.setup.GIT_BRANCH == var.setup.publish_latest_docker_image %}
docker tag {{ var.setup.docker_registry_org_unit }}/{{ context }}:${REVISION} \
    {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_org_unit }}/{{ context }}:latest
{% endif -%}
{% endif -%}
{% endfor -%}

if [ "${DOCKER_REGISTRY_PASSWORD}" == "" ] ; then
    echo "No docker registry password set in DOCKER_REGISTRY_PASSWORD -> no upload of images"
else
    echo "Logging into {{ var.setup.docker_registry}} as {{ var.setup.docker_registry_user }}..."
    echo ${DOCKER_REGISTRY_PASSWORD} | \
         docker login {{ var.setup.docker_registry}} --username  {{ var.setup.docker_registry_user }} --password-stdin
    {% for (context, upload) in var.setup.docker_contexts -%}
    {% if upload -%}
    echo "Uploading docker image in context directory '{{ context }}'..."
    docker push {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_org_unit }}/{{ context }}:${REVISION}
    {% if var.setup.GIT_BRANCH == var.setup.publish_latest_docker_image %}
    docker push {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_org_unit }}/{{ context }}:latest
    {% endif -%}
    {% endif -%}
    {% endfor -%}
    echo "Logging out from {{ var.setup.docker_registry}}..."
    docker logout {{ var.setup.docker_registry}}
fi
