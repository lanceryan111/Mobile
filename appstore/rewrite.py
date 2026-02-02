明白了，你要去掉 Vault 依赖，直接传入 API 凭证。我来帮你改写：

**图2 - `checkProfilesAndCertificates` 改写：**

```ruby
def checkProfilesAndCertificates(apiKey, issuerID, keyID, now)
  # 1. create a JWT token (直接用传入的参数)
  jwt = generateJWT(apiKey, issuerID, keyID, 60)
  
  # 2. fetch profiles and certificates from app store connect
  conn = AppStoreConnectProfiles.new(jwt)
  conn.fetchProfiles
  conn.fetchDistributionCertificates
  
  # 3. check profiles
  prof = conn.getProfiles
  resProfiles = checkProfiles(prof, now)
  
  # 4. check certificates
  certs = conn.getCertificates
  resCerts = checkCertificates(certs, now)
  
  return resProfiles, resCerts
end

# 新的 JWT 生成方法（不依赖 Vault）
def generateJWT(apiKey, issuerID, keyID, ttlSeconds)
  private_key = OpenSSL::PKey.read(apiKey)
  
  token = JWT.encode(
    {
      iss: issuerID,
      exp: Time.now.to_i + ttlSeconds,
      aud: "appstoreconnect-v1"
    },
    private_key,
    "ES256",
    header_fields={
      kid: keyID
    }
  )
end
```

**图1 - `checkAllAppstores` 改写：**

```ruby
def checkAllAppstores(appStoreCredentials, now)
  # appStoreCredentials 是一个 hash，包含每个 appstore 的凭证
  # 例如: {
  #   'appstore-main' => { apiKey: '...', issuerID: '...', keyID: '...' },
  #   'appstore-tdi' => { apiKey: '...', issuerID: '...', keyID: '...' }
  # }
  
  resAppStores = []
  resProfiles = []
  resCertificates = []
  
  appStoreCredentials.each do |appStore, creds|
    # 1. check in app store
    prof, certs = checkProfilesAndCertificates(
      creds[:apiKey],
      creds[:issuerID],
      creds[:keyID],
      now
    )
    
    # 2. aggregate results
    resAppStores.push appStore
    resProfiles.push prof
    resCertificates.push certs
  end
  
  return resAppStores, resProfiles, resCertificates
end
```

**调用方式（在 `checkAll` 或入口处）：**

```ruby
def checkAll(appStoreCredentials)
  now = DateTime.now
  
  # 1. Appstore Connect
  appStores, appStoreProfiles, appStoreCertificates = checkAllAppstores(appStoreCredentials, now)
  
  # 2. Local APNS certificates
  # ...
end

# 入口调用示例
credentials = {
  'appstore-main' => {
    apiKey: ENV['MAIN_API_KEY'],
    issuerID: ENV['MAIN_ISSUER_ID'],
    keyID: ENV['MAIN_KEY_ID']
  },
  'appstore-tdi' => {
    apiKey: ENV['TDI_API_KEY'],
    issuerID: ENV['TDI_ISSUER_ID'],
    keyID: ENV['TDI_KEY_ID']
  }
}

checkAll(credentials)
```

这样你就可以在 GitHub Actions 里通过环境变量或 secrets 传入这 6 个参数了。​​​​​​​​​​​​​​​​