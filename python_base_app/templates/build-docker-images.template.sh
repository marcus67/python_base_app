#!/usr/bin/env bash
SCRIPT_DIR=$(dirname $0)
BASE_DIR=$(realpath ${SCRIPT_DIR}/..)

DEBIAN_PACKAGE_BASE_NAME={{ var.setup.debian_package_name }}_{{ var.setup.version }}_{{ var.setup.debian_package_revision }}
DEBIAN_PACKAGE_NAME={{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}.deb

{% for context in var.setup.docker_contexts %}
echo "Build docker image in context directory {{ context }}..."
CONTEXT_DIR=${BASE_DIR}/{{ var.setup.docker_context_dir }}/{{ context }}
ASSETS_DIR=${CONTEXT_DIR}/assets

if [ -d ${CONTEXT_DIR} ]; then
    cp -a ${DEBIAN_PACKAGE_NAME} ${ASSETS_DIR}/{{ var.setup.debian_package_name }}.deb
fi

docker build -t {{ var.setup.docker_hub_user }}/{{ context }}:{{ var.setup.debian_package_revision }} --build-arg TAG={{ var.setup.debian_package_revision }} ${CONTEXT_DIR}
docker tag {{ var.setup.docker_hub_user }}/{{ context }}:{{ var.setup.debian_package_revision }} {{ var.setup.docker_hub_user }}/{{ context }}:latest
{% endfor %}
