- name: Debug Maven & Gradle Config
  run: |
    echo "=== Machine Info ==="
    hostname
    sw_vers
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
    find ~/Library/Caches/gradle -path "*threatmetrix*" -print 2>/dev/null || echo "not in Library"
    find ~/.gradle/caches -path "*threatmetrix*" -print 2>/dev/null || echo "not in .gradle"
    find ~/.gradle/caches -name "TMXProfiling-7.6-46.pom" -exec shasum -a 256 {} \;
    find ~/Library/Caches/gradle -name "TMXProfiling-7.6-46.pom" -exec shasum -a 256 {} \;

    echo "=== Gradle Home ==="
    echo "GRADLE_USER_HOME=${GRADLE_USER_HOME:-~/.gradle}"
    ls -la "${GRADLE_USER_HOME:-$HOME/.gradle}"/init.d/ 2>/dev/null || echo "no init.d"

    echo "=== Env vars (maven related) ==="
    env | grep -iE "maven|artifactory|nexus|repo|registry|gradle" || echo "none"
  shell: bash
