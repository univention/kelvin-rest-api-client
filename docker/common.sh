# to be sourced by build_ucs_join_image or build_udm_rest_api_only_image

UCS_REPOS="stable"

export DOCKER_REGISTRY="docker.software-univention.de"
export UCS_VERSION="4.4-8"

export UCS_CONTAINER=udm_rest_only
export UCS_JOINED_TARGET_DOCKER_IMG="${DOCKER_REGISTRY}/ucs-master-amd64-joined"
export UCS_JOINED_TARGET_DOCKER_IMG_VERSION="${UCS_JOINED_TARGET_DOCKER_IMG}:${UCS_REPOS}-${UCS_VERSION}"
export UCS_JOINED_TARGET_DOCKER_IMG_LATEST="${UCS_JOINED_TARGET_DOCKER_IMG}:${UCS_REPOS}-latest"

export UDM_ONLY_PARENT_DOCKER_IMG="ucs-master-amd64-joined"
export UDM_ONLY_TARGET_DOCKER_IMG="${DOCKER_REGISTRY}/${UDM_ONLY_PARENT_DOCKER_IMG}-ucsschool-udm-rest-api-only"
export UDM_ONLY_TARGET_DOCKER_IMG_VERSION="${UDM_ONLY_TARGET_DOCKER_IMG}:${UCS_REPOS}-${UCS_VERSION}"
export UDM_ONLY_TARGET_DOCKER_IMG_LATEST="${UDM_ONLY_TARGET_DOCKER_IMG}:${UCS_REPOS}-latest"

export KELVIN_CONTAINER=kelvin-api
export KELVIN_REST_API_VERSION="1.5.5"
export KELVIN_REST_API_IMG="${DOCKER_REGISTRY}/ucsschool-kelvin-rest-api:${KELVIN_REST_API_VERSION}"
export KELVIN_API_LOG_FILE="/var/log/univention/ucsschool-kelvin-rest-api/http.log"


docker_img_exists () {
  local IMG="${1?:Missing image name}"
  [ -z "$IMG" ] && return 1
  docker images "$IMG" | grep -E -q -v '^REPOSITORY' && return 0
}

docker_container_running () {
  local CONTAINER="${1?:Missing container name}"
  [ -z "$CONTAINER" ] && return 1
  docker ps --filter name="$CONTAINER" | grep -E -q -v '^CONTAINER' && return 0
}

docker_container_ip () {
  local CONTAINER="${1?:Missing container name}"
  [ -z "$CONTAINER" ] && echo "Empty container name" && return 1
  docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER"
}

get_openapi_schema () {
  local CONTAINER="${1?:Missing container name}"
  [ -z "$CONTAINER" ] && echo "Empty container name" && return 1
  if [ "$CONTAINER" = "$UCS_CONTAINER" ]; then
      echo "Trying to download UDM OpenAPI schema..."
      if [ -z "$UCS_CONTAINER_IP" ]; then
        export UCS_CONTAINER_IP=$(docker_container_ip "$CONTAINER")
      fi
      [ -z "$UCS_CONTAINER_IP" ] && echo "Empty container IP" && return 1
      curl -s --fail -u Administrator:univention -X GET http://$UCS_CONTAINER_IP/univention/udm/openapi.json
  elif  [ "$CONTAINER" = "$KELVIN_CONTAINER" ]; then
      echo "Trying to download Kelvin OpenAPI schema..."
      if [ -z "$KELVIN_CONTAINER_IP" ]; then
        export KELVIN_CONTAINER_IP=$(docker_container_ip "$CONTAINER")
      fi
      [ -z "$KELVIN_CONTAINER_IP" ] && echo "Empty container IP" && return 1
      curl -s --fail -X GET "http://$KELVIN_CONTAINER_IP:8911/ucsschool/kelvin/v1/openapi.json"
  else
      echo "Unknown container name '$CONTAINER'."
      return 1
  fi
}
