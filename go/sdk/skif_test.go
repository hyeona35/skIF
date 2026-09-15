package skif
import "testing"
func TestClientBuild(t *testing.T){ c:=New("http://localhost:1","x"); if c.BaseURL!="http://localhost:1"{t.Fatal(c.BaseURL)} }
