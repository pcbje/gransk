set -e

apt-get install -y git

# Gransk
cd ~
git clone https://github.com/pcbje/gransk
cd ~/gransk
apt-get update
apt-get install --force-yes -y \
      python-dev python-setuptools zlib1g-dev p7zip-full python-pip libicu-dev
pip install -r requirements.txt
pip install -r utils/dfvfs-requirements.txt
pip install -U six

python setup.py install
python setup.py download
python run_tests.py

apt-get install --force-yes -y \
    nodejs nodejs-legacy npm openjdk-7-jdk fontconfig && \
    cd gransk/web/tests/ && rm -rf node_modules && npm install && cd ../../../ && \
    gransk/web/tests/node_modules/.bin/karma start gransk/web/tests/cover.conf.js && \
    rm -rf gransk/web/tests/node_modules && \
    apt-get remove --force-yes -y --purge \
        nodejs nodejs-legacy npm fontconfig && \
    apt-get --force-yes -y autoremove

# TIKA
TIKA_VERSION=1.14
TIKA_SERVER_URL=https://www.apache.org/dist/tika/tika-server-$TIKA_VERSION.jar

apt-get install openjdk-7-jre curl gdal-bin tesseract-ocr \
		tesseract-ocr-eng tesseract-ocr-ita tesseract-ocr-fra tesseract-ocr-spa tesseract-ocr-deu -y \
	&& curl -sSL https://people.apache.org/keys/group/tika.asc -o /tmp/tika.asc \
	&& gpg --import /tmp/tika.asc \
	&& curl -sSL "$TIKA_SERVER_URL.asc" -o /tmp/tika-server-${TIKA_VERSION}.jar.asc \
	&& NEAREST_TIKA_SERVER_URL=$(curl -sSL http://www.apache.org/dyn/closer.cgi/${TIKA_SERVER_URL#https://www.apache.org/dist/}\?asjson\=1 \
		| awk '/"path_info": / { pi=$2; }; /"preferred":/ { pref=$2; }; END { print pref " " pi; };' \
		| sed -r -e 's/^"//; s/",$//; s/" "//') \
	&& echo "Nearest mirror: $NEAREST_TIKA_SERVER_URL" \
	&& curl -sSL "$NEAREST_TIKA_SERVER_URL" -o /tika-server-${TIKA_VERSION}.jar \
	&& apt-get clean -y && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Elasticsearch
ES_PKG_NAME=elasticsearch-1.5.0
rm -rf /elasticsearch/$ES_PKG_NAME
cd / && \
  wget https://download.elasticsearch.org/elasticsearch/elasticsearch/$ES_PKG_NAME.tar.gz && \
  tar xvzf $ES_PKG_NAME.tar.gz && \
  rm -f $ES_PKG_NAME.tar.gz && \
  mv /$ES_PKG_NAME /elasticsearch

echo "path:" > /elasticsearch/config/elasticsearch.yml
echo "  data: /data/data" >> /elasticsearch/config/elasticsearch.yml
echo "  logs: /data/log" >> /elasticsearch/config/elasticsearch.yml
echo "  plugins: /data/plugins" >> /elasticsearch/config/elasticsearch.yml
echo "  work: /data/work" >> /elasticsearch/config/elasticsearch.yml

# Start services on boot
(crontab -l 2>/dev/null || true; echo "@reboot /elasticsearch/bin/elasticsearch -Des.http.cors.enabled=true -Dhttp.cors.allow-origin=* > /var/log/es.log 2>&1 &") | crontab -
(crontab -l 2>/dev/null; echo "@reboot java -jar /tika-server-1.14.jar -h 0.0.0.0 > /var/log/tika.log 2>&1 &") | crontab -
(crontab -l 2>/dev/null; echo "@reboot sleep 10 && python -m gransk.boot.ui --host=0.0.0.0 > /var/log/gransk.log 2>&1 &") | crontab -

echo "Gransk installation completed!"
