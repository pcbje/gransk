Invoke-WebRequest https://raw.githubusercontent.com/pcbje/gransk/master/docker-compose.yml -Outfile docker-compose.yml
docker-compose up -d
docker pull pcbje/gransk
Set-Variable -Name "IP" -Value "localhost"
Write-Host "Go to: http://$IP`:8084" -ForegroundColor DarkYellow
docker run -p 8084:8084 -i -t pcbje/gransk

