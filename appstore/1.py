看你的代码结构，我建议用 **hash 传凭证** 的方式，这样最清晰且易扩展。

**改写方案：**

```ruby
# 276行 - checkAllAppstores
def checkAllAppstores(appStoreCredentials, now)
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

# 295行 - checkAll
def checkAll(appStoreCredentials)
  now = DateTime.now
  
  # 1. Appstore Connect
  appStores, appStoreProfiles, appStoreCertificates = checkAllAppstores(appStoreCredentials, now)
  
  # 2. Local APNS certificates
  apns = localAPNCertificates
  localAPNS = checkAPNSCertificates(apns, now)
  
  # ... 后续逻辑
end
```

**入口调用（从环境变量读取）：**

```ruby
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

**GitHub Actions workflow 里设置这些环境变量：**

```yaml
env:
  MAIN_API_KEY: ${{ secrets.MAIN_API_KEY }}
  MAIN_ISSUER_ID: ${{ secrets.MAIN_ISSUER_ID }}
  MAIN_KEY_ID: ${{ secrets.MAIN_KEY_ID }}
  TDI_API_KEY: ${{ secrets.TDI_API_KEY }}
  TDI_ISSUER_ID: ${{ secrets.TDI_ISSUER_ID }}
  TDI_KEY_ID: ${{ secrets.TDI_KEY_ID }}
```

这样设计的好处是：如果以后加第三个 appstore，只需要在 credentials hash 里加一项就行，代码不用改。​​​​​​​​​​​​​​​​