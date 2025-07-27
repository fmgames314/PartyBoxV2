systemctl disable controller
cp controller.service /lib/systemd/system/controller.service
chmod 644 /lib/systemd/system/controller.service
systemctl enable controller
systemctl restart controller

systemctl disable webserver
cp webserver.service /lib/systemd/system/webserver.service
chmod 644 /lib/systemd/system/webserver.service
systemctl enable webserver
systemctl restart webserver

systemctl disable us_fft
cp us_fft.service /lib/systemd/system/us_fft.service
chmod 644 /lib/systemd/system/us_fft.service
systemctl enable us_fft
systemctl restart us_fft


