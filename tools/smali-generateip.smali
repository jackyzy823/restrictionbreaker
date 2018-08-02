/*
    public String generateIP(){
        //String ips=  "126.0.0.0";
        Random r = new Random();
        long ip = 2113929216+ r.nextLong() % 16777216;
//        int prefix = 8; // 126.0.0.0/8
//        int mask = 0xffffffff << (32 - prefix) ;
        return ((ip >> 24) & 0xFF) + "."
                + ((ip >> 16) & 0xFF) + "."
                + ((ip >> 8) & 0xFF) + "."
                + (ip & 0xFF);
    }

    public void forceSetXForwardForViaCasting(){
        this.datafactory = new OkHttpDataSourceFactory(client, "aaaaaaa", new TransferListener<DataSource>() {
            @Override
            public void onTransferStart(DataSource source, DataSpec dataSpec) {

            }

            @Override
            public void onBytesTransferred(DataSource source, int bytesTransferred) {

            }

            @Override
            public void onTransferEnd(DataSource source) {

            }
        });
        HttpDataSource dt = (HttpDataSource) datafactory.createDataSource();
        dt.setRequestProperty("X-Forwarded-For",generateIP());
        DataSource ds = (DataSource)dt;
        ds.getUri();
    }

*/

# virtual methods
.method public generateIP()Ljava/lang/String;
    .locals 11

    .line 30
    new-instance v0, Ljava/util/Random;

    invoke-direct {v0}, Ljava/util/Random;-><init>()V

    .line 31
    .local v0, "r":Ljava/util/Random;
    invoke-virtual {v0}, Ljava/util/Random;->nextLong()J

    move-result-wide v1
    # /8
    const-wide/32 v3, 0x1000000

    rem-long/2addr v1, v3
    # 126.0.0.0
    const-wide/32 v3, 0x7e000000

    add-long v5, v3, v1

    .line 34
    .local v5, "ip":J
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const/16 v2, 0x18

    shr-long v2, v5, v2

    const-wide/16 v7, 0xff

    and-long v9, v2, v7

    invoke-virtual {v1, v9, v10}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    const-string v2, "."

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const/16 v2, 0x10

    shr-long v2, v5, v2

    and-long v9, v2, v7

    invoke-virtual {v1, v9, v10}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    const-string v2, "."

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const/16 v2, 0x8

    shr-long v2, v5, v2

    and-long v9, v2, v7

    invoke-virtual {v1, v9, v10}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    const-string v2, "."

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    and-long v2, v5, v7

    invoke-virtual {v1, v2, v3}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    return-object v1
.end method



tv.abema.i.a.h aka .source "AbemaOnlineDataSourceFactory.java"
smali_classes2/tv/abema/i/a/h.smali
# virtual methods
.method public bEE()Ltv/abema/i/a/b;
    .locals 6

    .prologue
    .line 41
    new-instance v0, Ltv/abema/i/a/g;

    iget-object v1, p0, Ltv/abema/i/a/h;->baseDataSourceFactory:Lcom/google/android/exoplayer2/upstream/DataSource$Factory;

    invoke-interface {v1}, Lcom/google/android/exoplayer2/upstream/DataSource$Factory;->createDataSource()Lcom/google/android/exoplayer2/upstream/DataSource;

    move-result-object v1
    
    #change start
    check-cast v1, Lcom/google/android/exoplayer2/upstream/HttpDataSource;

    const-string v2, "X-Forwarded-For"

    invoke-virtual {p0}, Ltv/abema/i/a/h;->generateIP()Ljava/lang/String;

    move-result-object v3

    invoke-interface {v1, v2, v3}, Lcom/google/android/exoplayer2/upstream/HttpDataSource;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    #change end