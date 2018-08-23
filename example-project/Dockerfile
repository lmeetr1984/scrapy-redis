#@IgnoreInspection BashAddShebang

# 
FROM python:2.7-onbuild

########## REQUIRED DEPENDENCIES ################
RUN mkdir ~/.pip && \
    cd ~/.pip/  && \
    echo "[global] \
    index-url = http://pypi.tuna.tsinghua/simple \
    trusted-host = \
    pypi.tuna.tsinghua \
    timeout = 120 \
   	" >  pip.conf

ENTRYPOINT ["scrapy"]
CMD ["crawl", "dmoz"]
