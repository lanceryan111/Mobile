- name: Debug Maven & Gradle Config
  run: |
    echo "=== Machine Info ==="
    hostname
    uname -a
    java -version
    ./gradlew --version

    echo "=== Gradle Init Scripts ==="
    ls -la ~/.gradle/init.d/ 2>/dev/null || echo "no init.d"
    cat ~/.gradle/init.d/*.gradle 2>/dev/null || echo "no init scripts"

    echo "=== Gradle Properties ==="
    cat ~/.gradle/gradle.properties 2>/dev/null || echo "no gradle.properties"
    cat gradle.properties 2>/dev/null || echo "no project gradle.properties"

    echo "=== All Repositories ==="
    ./gradlew :apps:mobileBanking:repositories

    echo "=== TMX in cache ==="
    find ~/.gradle/caches -path "*threatmetrix*" -ls 2>/dev/null || echo "not found"
    find ~/.gradle/caches -name "TMXProfiling-7.6-46.pom" -exec shasum -a 256 {} \;

    echo "=== Env vars (maven related) ==="
    env | grep -iE "maven|artifactory|nexus|repo|registry" || echo "none"
  shell: bash
