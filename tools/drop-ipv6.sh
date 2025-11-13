# Or flush all rules and set default DROP
sudo ip6tables -F
sudo ip6tables -X
sudo ip6tables -P INPUT DROP
sudo ip6tables -P FORWARD DROP
sudo ip6tables -P OUTPUT DROP

