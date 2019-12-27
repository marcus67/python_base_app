#!/usr/bin/env bash
SCRIPT_DIR=$(dirname $0)
BASE_DIR=$(realpath ${SCRIPT_DIR}/..)

DEBIAN_PACKAGE_BASE_NAME={{ var.setup.debian_package_name }}_{{ var.setup.version }}_{{ var.setup.debian_package_revision }}
DEBIAN_PACKAGE_NAME=${BASE_DIR}/{{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}.deb

{% for (context, upload) in var.setup.docker_contexts %}
echo "Build docker image in context directory '{{ context[0] }}'..."
CONTEXT_DIR=${BASE_DIR}/{{ var.setup.docker_context_dir }}/{{ context }}
ASSETS_DIR=${CONTEXT_DIR}/assets

if [ -d ${CONTEXT_DIR} ]; then
    cp -a ${DEBIAN_PACKAGE_NAME} ${ASSETS_DIR}/{{ var.setup.debian_package_name }}.deb
fi

docker build -t {{ var.setup.docker_registry_user }}/{{ context }}:{{ var.setup.debian_package_revision }} \
    --build-arg TAG={{ var.setup.debian_package_revision }} ${CONTEXT_DIR}
docker tag {{ var.setup.docker_registry_user }}/{{ context }}:{{ var.setup.debian_package_revision }} \
    {{ var.setup.docker_registry_user }}/{{ context }}:latest
{% if upload -%}
docker tag {{ var.setup.docker_registry_user }}/{{ context }}:{{ var.setup.debian_package_revision }} \
    {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_user }}/{{ context }}:{{ var.setup.debian_package_revision }}
docker tag {{ var.setup.docker_registry_user }}/{{ context }}:{{ var.setup.debian_package_revision }} \
    {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_user }}/{{ context }}:latest
{% endif -%}
{% endfor -%}

if [ "${DOCKER_REGISTRY_PASSWORD}" == "" ] ; then
    echo "No docker registry password set in DOCKER_REGISTRY_PASSWORD."
else
    echo "Logging into {{ var.setup.docker_registry}} as {{ var.setup.docker_registry_user }}..."
    docker login {{ var.setup.docker_registry}} --username  {{ var.setup.docker_registry_user }} --password ${DOCKER_REGISTRY_PASSWORD}
fi

{% for (context, upload) in var.setup.docker_contexts -%}
{% if upload -%}
echo "Uploading docker image in context directory '{{ context }}'..."
docker push {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_user }}/{{ context }}:{{ var.setup.debian_package_revision }}
docker push {{ var.setup.docker_registry}}/{{ var.setup.docker_registry_user }}/{{ context }}:latest
{% endif -%}
{% endfor -%}

if [ "${DOCKER_REGISTRY_PASSWORD}" != "" ] ; then
    echo "Logging out from {{ var.setup.docker_registry}}..."
    docker logout {{ var.setup.docker_registry}}
fi
