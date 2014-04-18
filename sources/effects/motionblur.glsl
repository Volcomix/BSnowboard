uniform sampler2D sceneSampler;
uniform sampler2D depthTexture;

uniform mat4 viewProjectionInverseMatrix;
uniform mat4 previousViewProjectionMatrix;

uniform float numSamples;
uniform float detail;

void main(void)
{
    vec2 texCoord = gl_TexCoord[0].st;
    vec4 color = texture2D(sceneSampler, texCoord);
    float depth = float(texture2D(depthTexture, texCoord));
    if (color.a == 1.0)
    {
        vec4 H = vec4(texCoord.x * 2 - 1, (1 - texCoord.y) * 2 - 1, depth, 1);
        vec4 D = H * viewProjectionInverseMatrix;
        vec4 worldPos = D / D.w;
        
        vec4 currentPos = H;
        vec4 previousPos = worldPos * previousViewProjectionMatrix;
        previousPos /= previousPos.w;
        vec2 velocity = vec2(currentPos - previousPos) / detail;
        
        int addedSamples = 1;
        texCoord += velocity;
        for(int i = 1; i < numSamples; ++i, texCoord += velocity)
        {
            vec4 currentColor = texture2D(sceneSampler, texCoord);
            if (currentColor.a == 1.0)
            {
                color += currentColor;
                addedSamples++;
            }
        }
        gl_FragColor = color / addedSamples;
    }
    else
    {
        gl_FragColor = color;
    }
}