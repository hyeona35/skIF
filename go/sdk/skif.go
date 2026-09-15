package skif
import("bytes";"encoding/json";"fmt";"io";"net/http";"net/url";"strings";"time")
type Client struct{BaseURL,Token string;HTTP *http.Client}
func New(baseURL,token string)*Client{return &Client{BaseURL:strings.TrimRight(baseURL,"/"),Token:token,HTTP:&http.Client{Timeout:30*time.Second}}}
func(c *Client) Do(path string,payload any,method string)(map[string]any,error){var r io.Reader=nil;if payload!=nil{b,_:=json.Marshal(payload);r=bytes.NewReader(b)};req,err:=http.NewRequest(method,c.BaseURL+path,r);if err!=nil{return nil,err};req.Header.Set("Content-Type","application/json");if c.Token!=""{req.Header.Set("Authorization","Bearer "+c.Token)};resp,err:=c.HTTP.Do(req);if err!=nil{return nil,err};defer resp.Body.Close();raw,_:=io.ReadAll(resp.Body);var out map[string]any;_ = json.Unmarshal(raw,&out);if resp.StatusCode>=300{return out,fmt.Errorf("skIF HTTP %d: %s",resp.StatusCode,string(raw))};return out,nil}
func(c *Client) Capabilities(agentID string,caps []string)(map[string]any,error){return c.Do("/api/agents/capabilities",map[string]any{"agent_id":agentID,"capabilities":caps},http.MethodPost)}
func(c *Client) Telemetry(eventType,agentID string,payload map[string]any)(map[string]any,error){return c.Do("/api/telemetry",map[string]any{"event_type":eventType,"agent_id":agentID,"payload":payload},http.MethodPost)}
func(c *Client) Recommend(task string)(map[string]any,error){return c.Do("/api/agent/recommend?task="+url.QueryEscape(task),nil,http.MethodGet)}
func(c *Client) TeamPlan(payload map[string]any)(map[string]any,error){return c.Do("/api/agent/team/plan",payload,http.MethodPost)}
func(c *Client) KnowledgePath(source,target string)(map[string]any,error){return c.Do("/api/knowledge/mesh/path?source="+url.QueryEscape(source)+"&target="+url.QueryEscape(target),nil,http.MethodGet)}
func(c *Client) Contribution(agentID,skillID,action,summary string)(map[string]any,error){return c.Do("/api/contributions",map[string]any{"agent_id":agentID,"skill_id":skillID,"action":action,"summary":summary},http.MethodPost)}
